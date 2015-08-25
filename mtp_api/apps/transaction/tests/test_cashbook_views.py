import random
import urllib.parse

from django.core.urlresolvers import reverse
from django.utils.six.moves.urllib.parse import urlsplit

from rest_framework import status

from mtp_auth.models import PrisonUserMapping

from transaction.models import Log
from transaction.constants import TRANSACTION_STATUS, LOCK_LIMIT, LOG_ACTIONS

from .test_base import BaseTransactionViewTestCase, \
    TransactionRejectsRequestsWithoutPermissionTestMixin


def get_users_for_prison(prison):
    return [m.user for m in PrisonUserMapping.objects.filter(prisons=prison)]


def get_prisons_for_user(user):
    return PrisonUserMapping.objects.get(user=user).prisons.all()


class CashbookTransactionRejectsRequestsWithoutPermissionTestMixin(
    TransactionRejectsRequestsWithoutPermissionTestMixin
):

    def _get_unauthorised_application_users(self):
        return [
            self.bank_admins[0], self.prisoner_location_admins[0]
        ]

    def _get_authorised_user(self):
        return self.prison_clerks[0]


class TransactionListTestCase(BaseTransactionViewTestCase):

    def test_cant_access(self):
        """
        GET on transactions endpoint should 403.
        """
        url = reverse('cashbook:transaction-list')

        # authenticate, just in case
        prison = [t.prison for t in self.transactions if t.prison][0]
        user = get_users_for_prison(prison)[0]

        response = self.client.get(
            url, format='json',
            HTTP_AUTHORIZATION=self.get_http_authorization_for_user(user)
        )
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN
        )


class TransactionListByPrisonTestCase(
    CashbookTransactionRejectsRequestsWithoutPermissionTestMixin,
    BaseTransactionViewTestCase
):

    def _request_and_assert(self, status_param=None):
        for prison in self.prisons:
            expected_ids = [
                t.pk for t in self.transactions if
                    t.prison == prison and
                    self.STATUS_FILTERS[status_param](t)
            ]

            expected_owners = get_users_for_prison(prison)
            user = expected_owners[0]

            url = self._get_url(user, prison, status=status_param)
            response = self.client.get(
                url, format='json',
                HTTP_AUTHORIZATION=self.get_http_authorization_for_user(user)
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['count'], len(expected_ids))

            self.assertListEqual(
                sorted([t['id'] for t in response.data['results']]),
                sorted(expected_ids)
            )

    def _get_url(self, user, prison, status=None):
        url = reverse(
            'cashbook:transaction-prison-list', kwargs={
                'prison_id': prison.pk
            }
        )

        params = {
            'limit': 10000
        }
        if status:
            params['status'] = status

        return '{url}?{params}'.format(
            url=url, params=urllib.parse.urlencode(params)
        )

    def test_fails_with_logged_in_managing_different_prison(self):
        """
        Tests that users managing a prison cannot access any
        transactions belonging to other prisons.
        """
        logged_in_user_prison = self.prisons[0]
        other_prison = self.prisons[1]

        logged_in_user = get_users_for_prison(logged_in_user_prison)[0]

        url = self._get_url(logged_in_user, other_prison)

        response = self.client.get(
            url, format='json',
            HTTP_AUTHORIZATION=self.get_http_authorization_for_user(logged_in_user)
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_all(self):
        """
        GET without params should return all transactions linked
        to that prison.
        """
        self._request_and_assert()

    def test_with_locked_status(self):
        self._request_and_assert(
            status_param=TRANSACTION_STATUS.LOCKED
        )

    def test_with_available_status(self):
        self._request_and_assert(
            status_param=TRANSACTION_STATUS.AVAILABLE
        )

    def test_with_credited_status(self):
        self._request_and_assert(
            status_param=TRANSACTION_STATUS.CREDITED
        )


class TransactionListByPrisonAndUserTestCase(
    CashbookTransactionRejectsRequestsWithoutPermissionTestMixin,
    BaseTransactionViewTestCase
):

    def _request_and_assert(self, status_param=None):
        for owner in self.prison_clerks:
            prisons = get_prisons_for_user(owner)

            for prison in prisons:
                expected_ids = [
                    t.pk for t in self.transactions if
                        t.prison == prison and
                        t.owner == owner and
                        self.STATUS_FILTERS[status_param](t)
                ]
                url = self._get_url(owner, prison, status=status_param)

                response = self.client.get(
                    url, format='json',
                    HTTP_AUTHORIZATION=self.get_http_authorization_for_user(owner)
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data['count'], len(expected_ids))

                self.assertListEqual(
                    sorted([t['id'] for t in response.data['results']]),
                    sorted(expected_ids)
                )

    def _get_url(self, user, prison, status=None):
        url = reverse(
            'cashbook:transaction-prison-user-list', kwargs={
                'user_id': user.pk,
                'prison_id': prison.pk
            }
        )

        params = {
            'limit': 10000
        }
        if status:
            params['status'] = status

        return '{url}?{params}'.format(
            url=url, params=urllib.parse.urlencode(params)
        )

    def test_fails_with_logged_in_managing_different_prison(self):
        """
        Tests that users managing a prison cannot access any
        transactions belonging to other prisons.
        """
        logged_in_user_prison = self.prisons[0]
        other_prison = self.prisons[1]

        logged_in_user = get_users_for_prison(logged_in_user_prison)[0]
        other_user = get_users_for_prison(other_prison)[0]

        url = self._get_url(other_user, other_prison)

        response = self.client.get(
            url, format='json',
            HTTP_AUTHORIZATION=self.get_http_authorization_for_user(logged_in_user)
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_all(self):
        self._request_and_assert()

    def test_with_locked_status(self):
        self._request_and_assert(
            status_param=TRANSACTION_STATUS.LOCKED
        )

    def test_with_available_status(self):
        self._request_and_assert(
            status_param=TRANSACTION_STATUS.AVAILABLE
        )

    def test_with_credited_status(self):
        self._request_and_assert(
            status_param=TRANSACTION_STATUS.CREDITED
        )


class TransactionsLockTestCase(
    CashbookTransactionRejectsRequestsWithoutPermissionTestMixin,
    BaseTransactionViewTestCase
):
    ENDPOINT_VERB = 'post'

    def _get_url(self, user, prison, count=None):
        url = reverse(
            'cashbook:transaction-prison-user-lock', kwargs={
                'user_id': user.pk,
                'prison_id': prison.pk
            }
        )

        if count:
            url += '?count={count}'.format(count=count)

        return url

    def test_lock_within_limit(self):
        """
        Tests that requesting n transactions with n <= LOCK_LIMIT
        should work.
        """
        prison = self.prisons[0]
        owner = get_users_for_prison(prison)[0]

        count = 1

        # delete locked transactions just to clean things up
        self._get_locked_transactions_qs(prison, owner).delete()

        # check no locked transactions in db
        self.assertEqual(
            self._get_locked_transactions_qs(prison, owner).count(),
            0
        )

        # request
        url = self._get_url(owner, prison, count)
        response = self.client.post(
            url, format='json',
            HTTP_AUTHORIZATION=self.get_http_authorization_for_user(owner)
        )

        self.assertEqual(response.status_code, status.HTTP_303_SEE_OTHER)
        self.assertEqual(
            urlsplit(response['Location']).path,
            reverse(
                'cashbook:transaction-prison-user-list', kwargs={
                    'user_id': owner.pk,
                    'prison_id': prison.pk
                }
            )
        )

        # check 5 locked transactions in db
        locked_transactions = self._get_locked_transactions_qs(prison, owner)
        self.assertEqual(locked_transactions.count(), count)

        # check logs
        self.assertEqual(
            Log.objects.filter(
                user=owner,
                action=LOG_ACTIONS.LOCKED,
                transaction__id__in=locked_transactions.values_list('id', flat=True)
            ).count(),
            count
        )

    def test_nobody_else_can_lock_transactions_for_others(self):
        """
        Tests that nobody managing a prison should be able to
        lock transactions on behalf of other users.
        """
        prison = self.prisons[0]
        users = get_users_for_prison(prison)
        self.assertTrue(len(users) >= 2)

        # We need 2 users as we want to test that logged_in_user
        # cannot lock transactions on behalf of transactions_owner.
        logged_in_user = users[0]
        transactions_owner = users[1]

        # delete locked transactions just to clean things up
        self._get_locked_transactions_qs(prison, transactions_owner).delete()

        # check no locked transactions in db
        self.assertEqual(
            self._get_locked_transactions_qs(prison, transactions_owner).count(),
            0
        )

        # request
        url = self._get_url(transactions_owner, prison, 1)
        response = self.client.post(
            url, format='json',
            HTTP_AUTHORIZATION=self.get_http_authorization_for_user(logged_in_user)
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # check no locked transactions in db as the request failed
        self.assertEqual(
            self._get_locked_transactions_qs(prison, transactions_owner).count(),
            0
        )

    def test_fails_when_locking_too_many(self):
        """
        Tests that fails when trying to lock more than LOCK_LIMIT.
        """
        user = self.prison_clerks[0]
        prison = get_prisons_for_user(user)[0]

        # clean things up
        self._get_locked_transactions_qs(prison).update(owner=None)

        # make sure we have enough available transactions
        self.assertTrue(
            self._get_available_transactions_qs(prison).count() > LOCK_LIMIT
        )

        # check no locked transactions in db
        self.assertEqual(
            self._get_locked_transactions_qs(prison, user).count(), 0
        )

        http_authorization_header = self.get_http_authorization_for_user(user)

        # request LOCK_LIMIT-1
        count = LOCK_LIMIT-1

        url = self._get_url(user, prison, count)
        response = self.client.post(
            url, format='json',
            HTTP_AUTHORIZATION=http_authorization_header
        )

        self.assertEqual(response.status_code, status.HTTP_303_SEE_OTHER)

        # check LOCK_LIMIT-1 locked transactions in db
        self.assertEqual(
            self._get_locked_transactions_qs(prison, user).count(), count
        )

        # request 2 more => should fail
        url = self._get_url(user, prison, 2)
        response = self.client.post(
            url, format='json',
            HTTP_AUTHORIZATION=http_authorization_header
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # check still LOCK_LIMIT-1 locked transactions in db
        self.assertEqual(
            self._get_locked_transactions_qs(prison, user).count(), count
        )


class TransactionsUnlockTestCase(
    CashbookTransactionRejectsRequestsWithoutPermissionTestMixin,
    BaseTransactionViewTestCase
):
    ENDPOINT_VERB = 'post'

    def _get_url(self, user, prison):
        return reverse(
            'cashbook:transaction-prison-user-unlock', kwargs={
                'user_id': user.pk,
                'prison_id': prison.pk
            }
        )

    def test_cannot_unlock_somebody_else_s_transactions_in_different_prison(self):
        """
        Tests that logged_in_user managing prison1 cannot unlock any
        transactions for prison2.
        """
        prison1 = self.prisons[0]
        prison2 = self.prisons[1]

        logged_in_user = get_users_for_prison(prison1)[0]
        transactions_owner = get_users_for_prison(prison2)[0]

        locked_transactions = list(
            self._get_locked_transactions_qs(prison2, transactions_owner)
        )

        # if this starts failing, we need to iterate over users and get the
        # first user with locked transactions.
        self.assertTrue(len(locked_transactions) > 0)

        # request
        url = self._get_url(transactions_owner, prison2)
        response = self.client.post(
            url,
            {'transaction_ids': [t.id for t in locked_transactions]},
            format='json',
            HTTP_AUTHORIZATION=self.get_http_authorization_for_user(logged_in_user)
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_unlock_somebody_else_s_transactions(self):
        """
        Tests that anybody managing the same prison can unlock
        somebody else's locked transactions.
        """
        # We need 2 users as we want to test that logged_in_user
        # can unlock transactions on behalf of transactions_owner.
        prison = self.prisons[0]
        users = get_users_for_prison(prison)
        self.assertTrue(len(users) >= 2)

        logged_in_user = users[0]
        transactions_owner = users[1]

        locked_transactions = list(
            self._get_locked_transactions_qs(prison, transactions_owner)
        )

        # if this starts failing, we need to iterate over users and get the
        # first user with locked transactions.
        self.assertTrue(len(locked_transactions) > 0)

        # how many transactions should we unlock?
        to_unlock = random.randint(1, len(locked_transactions))
        transactions_to_unlock = locked_transactions[:to_unlock]

        currently_available = self._get_available_transactions_qs(prison).count()

        # request
        url = self._get_url(transactions_owner, prison)
        response = self.client.post(
            url,
            {'transaction_ids': [t.id for t in transactions_to_unlock]},
            format='json',
            HTTP_AUTHORIZATION=self.get_http_authorization_for_user(logged_in_user)
        )

        self.assertEqual(response.status_code, status.HTTP_303_SEE_OTHER)
        self.assertEqual(
            urlsplit(response['Location']).path,
            reverse(
                'cashbook:transaction-prison-user-list', kwargs={
                    'user_id': transactions_owner.pk,
                    'prison_id': prison.pk
                }
            )
        )

        # check locked transactions == -to_unlock
        self.assertEqual(
            self._get_locked_transactions_qs(prison, transactions_owner).count(),
            len(locked_transactions) - to_unlock
        )

        # check that available transactions == +to_unlock
        self.assertEqual(
            self._get_available_transactions_qs(prison).count(),
            currently_available + to_unlock
        )

        # check logs
        self.assertEqual(
            Log.objects.filter(
                user=logged_in_user, action=LOG_ACTIONS.UNLOCKED,
                transaction__id__in=[t.id for t in transactions_to_unlock]
            ).count(),
            to_unlock
        )

    def test_cannot_unlock_transactions_with_mismatched_url(self):
        """
        Tests that if we try to unlock all transactions_owner's
        locked transactions + a logged_in_user locked transaction
        =>
        it fails
        """
        prison = self.prisons[0]
        users = get_users_for_prison(prison)
        self.assertTrue(len(users) >= 2)

        logged_in_user = users[0]
        transactions_owner = users[1]

        prison = get_prisons_for_user(transactions_owner)[0]

        locked_transactions_owner = list(
            self._get_locked_transactions_qs(prison, transactions_owner)
        )
        locked_transactions_logged_in = list(
            self._get_locked_transactions_qs(prison, logged_in_user)
        )

        # if this starts failing, we need to iterate over users and get the
        # first user with locked transactions.
        self.assertTrue(len(locked_transactions_owner) > 0)
        self.assertTrue(len(locked_transactions_logged_in) > 0)

        transactions_to_unlock = locked_transactions_owner + locked_transactions_logged_in[:1]

        url = self._get_url(transactions_owner, prison)
        response = self.client.post(
            url,
            {'transaction_ids': [t.id for t in transactions_to_unlock]},
            format='json',
            HTTP_AUTHORIZATION=self.get_http_authorization_for_user(logged_in_user)
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # check nothing changed in the db
        self.assertEqual(
            self._get_locked_transactions_qs(prison, transactions_owner).count(),
            len(locked_transactions_owner)
        )

        self.assertEqual(
            self._get_locked_transactions_qs(prison, logged_in_user).count(),
            len(locked_transactions_logged_in)
        )

    def test_cannot_unlock_credited_transactions(self):
        """
        Tests that if we try to unlock all locked transactions +
        a credited transaction
        =>
        it fails
        """
        prison = self.prisons[0]
        users = get_users_for_prison(prison)
        self.assertTrue(len(users) >= 2)

        logged_in_user = users[0]
        transactions_owner = users[1]

        locked_transactions = list(
            self._get_locked_transactions_qs(prison, transactions_owner)
        )
        credited_transactions = list(
            self._get_credited_transactions_qs(transactions_owner, prison)
        )

        # if this starts failing, we need to iterate over users and get the
        # first user with locked transactions.
        self.assertTrue(len(locked_transactions) > 0)
        self.assertTrue(len(credited_transactions) > 0)

        transactions_to_unlock = locked_transactions + credited_transactions[:1]

        url = self._get_url(transactions_owner, prison)
        response = self.client.post(
            url,
            {'transaction_ids': [t.id for t in transactions_to_unlock]},
            format='json',
            HTTP_AUTHORIZATION=self.get_http_authorization_for_user(logged_in_user)
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # check nothing changed in the db
        self.assertEqual(
            self._get_locked_transactions_qs(prison, transactions_owner).count(),
            len(locked_transactions)
        )

        self.assertEqual(
            self._get_credited_transactions_qs(transactions_owner, prison).count(),
            len(credited_transactions)
        )


class TransactionsPatchTestCase(
    CashbookTransactionRejectsRequestsWithoutPermissionTestMixin,
    BaseTransactionViewTestCase
):
    ENDPOINT_VERB = 'patch'

    def _get_url(self, user, prison):
        return reverse(
            'cashbook:transaction-prison-user-list', kwargs={
                'user_id': user.pk,
                'prison_id': prison.pk
            }
        )

    def test_cannot_patch_somebody_else_s_transactions(self):
        """
        Tests that only the owner of a transaction (who loked it)
        can patch it.
        """
        prison = self.prisons[0]
        users = get_users_for_prison(prison)

        logged_in_user = users[0]
        transactions_owner = users[1]

        locked_transactions = list(
            self._get_locked_transactions_qs(prison, transactions_owner)
        )

        # if this starts failing, we need to iterate over users and get the
        # first user with locked transactions.
        self.assertTrue(len(locked_transactions) > 0)

        # request
        url = self._get_url(transactions_owner, prison)
        response = self.client.patch(
            url,
            {'transaction_ids': [t.id for t in locked_transactions]},
            format='json',
            HTTP_AUTHORIZATION=self.get_http_authorization_for_user(logged_in_user)
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_path_non_locked_transactions(self):
        """
        Tests that non-locked transactions cannot be marked as credited.
        """
        prison = self.prisons[0]
        user = get_users_for_prison(prison)[0]

        locked_transactions = list(
            self._get_locked_transactions_qs(prison, user)
        )

        available_transactions = list(
            self._get_available_transactions_qs(prison)
        )

        # if this starts failing, we need to iterate over users and get the
        # first user with locked transactions.
        self.assertTrue(len(locked_transactions) > 0)
        self.assertTrue(len(available_transactions) > 0)

        transactions_to_credit = locked_transactions + available_transactions[:1]

        # request
        url = self._get_url(user, prison)
        response = self.client.patch(
            url,
            {'transaction_ids': [t.id for t in transactions_to_credit]},
            format='json',
            HTTP_AUTHORIZATION=self.get_http_authorization_for_user(user)
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # check nothing changed in the db
        self.assertEqual(
            self._get_locked_transactions_qs(prison, user).count(),
            len(locked_transactions)
        )

        self.assertEqual(
            self._get_available_transactions_qs(prison).count(),
            len(available_transactions)
        )

    def test_mark_locked_transaction_as_credited(self):
        """
        Tests that locked owned transactions can be marked as
        credited.
        """
        prison = self.prisons[0]
        user = get_users_for_prison(prison)[0]

        locked_transactions = list(
            self._get_locked_transactions_qs(prison, user)
        )

        credited_transactions = list(
            self._get_credited_transactions_qs(user, prison)
        )

        # if this starts failing, we need to iterate over users and get the
        # first user with locked transactions.
        self.assertTrue(len(locked_transactions) > 0)

        # how many transactions should we credit?
        to_credit = random.randint(1, len(locked_transactions))
        transactions_to_credit = locked_transactions[:to_credit]

        # request
        url = self._get_url(user, prison)
        data = [
            {
                'id': t.id,
                'credited': True
            } for t in transactions_to_credit
        ]
        response = self.client.patch(
            url, data=data, format='json',
            HTTP_AUTHORIZATION=self.get_http_authorization_for_user(user)
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # check changes in db
        self.assertEqual(
            self._get_locked_transactions_qs(prison, user).count(),
            len(locked_transactions) - to_credit
        )

        self.assertEqual(
            self._get_credited_transactions_qs(user, prison).filter(id__in=[
                t.id for t in transactions_to_credit
            ]).count(),
            to_credit
        )

        self.assertEqual(
            self._get_credited_transactions_qs(user, prison).count(),
            len(credited_transactions) + to_credit
        )

        # check logs
        self.assertEqual(
            Log.objects.filter(
                user=user, action=LOG_ACTIONS.CREDITED,
                transaction__id__in=[t.id for t in transactions_to_credit]
            ).count(),
            to_credit
        )

    def test_invalid_data(self):
        """
        Tests that if the data passed to the patch endpoint is invalid
        =>
        it fails
        """
        prison = self.prisons[0]
        user = get_users_for_prison(prison)[0]

        locked_transactions = list(
            self._get_locked_transactions_qs(prison, user)
        )

        # if this starts failing, we need to iterate over users and get the
        # first user with locked transactions.
        self.assertTrue(len(locked_transactions) > 0)

        # how many transactions should we credit?
        to_credit = random.randint(1, len(locked_transactions))
        transactions_to_credit = locked_transactions[:to_credit]

        # request
        url = self._get_url(user, prison)

        # invalid data format
        invalid_data_list = [
            # invalid data format, should be a list not a dict
            {
                'msg': 'Invalid data format, dict instead of list',
                'data': {
                    'something': [
                        {
                            'id': t.id,
                            'credited': True
                        } for t in transactions_to_credit
                    ]
                },
            },

            # missing ids
            {
                'msg': 'Missing ids',
                'data': [
                    {
                        'credited': True
                    } for t in transactions_to_credit
                ],
            },

            # misspelt credited
            {
                'msg': 'Misspelt credited',
                'data': [
                    {
                        'id': t.id,
                        'credit': True
                    } for t in transactions_to_credit
                ]
            }
        ]
        for data in invalid_data_list:
            response = self.client.patch(
                url, data=data['data'], format='json',
                HTTP_AUTHORIZATION=self.get_http_authorization_for_user(user)
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                'Should fail because: {msg}'.format(msg=data['msg'])
            )
