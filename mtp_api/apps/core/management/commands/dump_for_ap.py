import argparse
import csv
import datetime
import textwrap

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_date

from credit.constants import CREDIT_STATUS
from credit.models import Credit, LOG_ACTIONS as CREDIT_LOG_ACTIONS
from disbursement.constants import DISBURSEMENT_METHOD, DISBURSEMENT_RESOLUTION
from disbursement.models import Disbursement, LOG_ACTIONS as DISBURSEMENT_LOG_ACTIONS
from transaction.utils import format_amount


class Command(BaseCommand):
    """
    Dump data for Analytical Platform
    """
    help = textwrap.dedent(__doc__).strip()

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--since', help='Since date (inclusive)')
        parser.add_argument('--until', help='Until date (exclusive)')
        parser.add_argument('type', choices=['credits', 'disbursements'], help='Type of object to dump')
        parser.add_argument('path', type=argparse.FileType('wt'), help='Path to dump data to')

    def handle(self, *args, **options):
        since = date_argument(options['since'])
        until = date_argument(options['until'])
        if since and until and until <= since:
            raise CommandError('"--until" must be after "--since"')

        object_type = options['type']
        writer = csv.DictWriter(options['path'], getattr(self, f'headers_{object_type}'))
        writer.writeheader()
        method = getattr(self, f'handle_{object_type}')
        for row in method(since, until):
            writer.writerow(row)

    headers_credits = [
        'Internal ID', 'URL',
        'Date received', 'Date credited',
        'Amount',
        'Prisoner number', 'Prisoner name', 'Prison',
        'Sender name', 'Payment method',
        'Bank transfer sort code', 'Bank transfer account', 'Bank transfer roll number',
        'Debit card number', 'Debit card expiry', 'Debit card billing address',
        'Sender email', 'Sender IP address',
        'Status',
        'NOMIS transaction',
    ]

    def handle_credits(self, since, until):
        if not since:
            since = Credit.objects.earliest().received_at
        if not until:
            until = Credit.objects.latest().received_at + datetime.timedelta(days=1)
            until.replace(hour=0, minute=0, second=0, microsecond=0)

        records = Credit.objects.filter(
            received_at__gte=since,
            received_at__lt=until,
        ).order_by('pk').iterator(chunk_size=1000)

        for record in records:
            status = record.status
            if status:
                status = CREDIT_STATUS.for_value(status).display
            else:
                status = 'Anonymous'
            row = {
                'Internal ID': record.id,
                'URL': f'{settings.NOMS_OPS_URL}/security/credits/{record.id}/',
                'Date received': record.received_at,
                'Date credited': find_log_date(record, CREDIT_LOG_ACTIONS.CREDITED),
                'Amount': format_amount(record.amount),
                'Prisoner number': record.prisoner_number or 'Unknown',
                'Prisoner name': record.prisoner_name or 'Unknown',
                'Prison': record.prison.short_name if record.prison else 'Unknown',
                'Status': status,
                'NOMIS transaction': record.nomis_transaction_id,
            }
            row.update(self.handle_credit_sender(record))
            yield row

    def handle_credit_sender(self, record: Credit):
        if hasattr(record, 'transaction'):
            transaction = record.transaction
            return {
                'Payment method': 'Bank transfer',
                'Sender name': transaction.sender_name,
                'Bank transfer sort code': transaction.sender_sort_code,
                'Bank transfer account': transaction.sender_account_number,
                'Bank transfer roll number': transaction.sender_roll_number,
            }

        if hasattr(record, 'payment'):
            payment = record.payment
            return {
                'Payment method': 'Debit card',
                'Sender name': payment.cardholder_name,
                'Debit card number': payment.card_number_last_digits,
                'Debit card expiry': payment.card_expiry_date,
                'Debit card billing address': str(payment.billing_address),
                'Sender email': payment.email,
                'Sender IP address': payment.ip_address,
            }

        return {
            'Payment method': 'Unknown',
            'Sender name': '(Unknown sender)',
        }

    headers_disbursements = [
        'Internal ID', 'URL',
        'Date entered', 'Date confirmed', 'Date sent',
        'Amount',
        'Prisoner number', 'Prisoner name', 'Prison',
        'Recipient name', 'Payment method',
        'Bank transfer sort code', 'Bank transfer account', 'Bank transfer roll number',
        'Recipient address', 'Recipient email',
        'Status',
        'NOMIS transaction', 'SOP invoice number',
    ]

    def handle_disbursements(self, since, until):
        if not since:
            since = Disbursement.objects.earliest().created
        if not until:
            until = Disbursement.objects.latest().created + datetime.timedelta(days=1)
            until.replace(hour=0, minute=0, second=0, microsecond=0)

        records = Disbursement.objects.filter(
            created__gte=since,
            created__lt=until,
        ).order_by('pk').iterator(chunk_size=1000)

        for record in records:
            yield {
                'Internal ID': record.id,
                'URL': f'{settings.NOMS_OPS_URL}/security/disbursements/{record.id}/',
                'Date entered': record.created,
                'Date confirmed': find_log_date(record, DISBURSEMENT_LOG_ACTIONS.CONFIRMED),
                'Date sent': find_log_date(record, DISBURSEMENT_LOG_ACTIONS.SENT),
                'Amount': format_amount(record.amount),
                'Prisoner number': record.prisoner_number,
                'Prisoner name': record.prisoner_name,
                'Prison': record.prison.short_name,
                'Recipient name': record.recipient_name,
                'Payment method': DISBURSEMENT_METHOD.for_value(record.method).display,
                'Bank transfer sort code': record.sort_code,
                'Bank transfer account': record.account_number,
                'Bank transfer roll number': record.roll_number,
                'Recipient address': record.recipient_address,
                'Recipient email': record.recipient_email,
                'Status': DISBURSEMENT_RESOLUTION.for_value(record.resolution).display,
                'NOMIS transaction': record.nomis_transaction_id,
                'SOP invoice number': record.invoice_number,
            }


def date_argument(argument):
    if not argument:
        return None
    date = parse_date(argument)
    if not date:
        raise CommandError('Cannot parse date')
    return timezone.make_aware(datetime.datetime.combine(date, datetime.time.min))


def find_log_date(record, action):
    log = record.log_set.filter(action=action).order_by('created').first()
    return log and log.created
