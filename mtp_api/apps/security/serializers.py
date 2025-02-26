from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.serializers import BasicUserSerializer
from prison.models import Prison
from security.models import (
    BankTransferRecipientDetails,
    BankTransferSenderDetails,
    Check,
    CheckAutoAcceptRule,
    CheckAutoAcceptRuleState,
    DebitCardSenderDetails,
    PrisonerProfile,
    RecipientProfile,
    SavedSearch,
    SearchFilter,
    SenderProfile,
)


class BankTransferSenderDetailsSerializer(serializers.ModelSerializer):
    sender_sort_code = serializers.CharField(
        source='sender_bank_account.sort_code'
    )
    sender_account_number = serializers.CharField(
        source='sender_bank_account.account_number'
    )
    sender_roll_number = serializers.CharField(
        source='sender_bank_account.roll_number'
    )

    class Meta:
        model = BankTransferSenderDetails
        fields = (
            'sender_name',
            'sender_sort_code',
            'sender_account_number',
            'sender_roll_number',
        )


class DebitCardSenderDetailsSerializer(serializers.ModelSerializer):
    cardholder_names = serializers.SerializerMethodField()
    sender_emails = serializers.SerializerMethodField()

    class Meta:
        model = DebitCardSenderDetails
        fields = (
            'card_number_last_digits',
            'card_expiry_date',
            'cardholder_names',
            'sender_emails',
            'postcode',
        )

    def get_cardholder_names(self, obj):
        return list(obj.cardholder_names.values_list('name', flat=True))

    def get_sender_emails(self, obj):
        return list(obj.sender_emails.values_list('email', flat=True))


class PrisonSerializer(serializers.ModelSerializer):
    """
    Serializer for nested prison fields.
    """

    # TODO Deduplicate this and prison.serializers.PrisonSerializer
    # so drf-yasg stops complaining about serializer namespace collisions
    # without custom ref name
    class Meta:
        ref_name = 'NOMIS Prison'
        model = Prison
        fields = (
            'nomis_id',
            'name',
        )


class SenderProfileSerializer(serializers.ModelSerializer):
    prisons = PrisonSerializer(many=True)

    bank_transfer_details = BankTransferSenderDetailsSerializer(many=True)
    debit_card_details = DebitCardSenderDetailsSerializer(many=True)

    # return None where this is a nested serializer
    prisoner_count = serializers.IntegerField(required=False)
    prison_count = serializers.IntegerField(required=False)
    monitoring = serializers.BooleanField(required=False)

    class Meta:
        model = SenderProfile
        fields = (
            'id',
            'credit_count',
            'credit_total',
            'prisons',
            'prisoner_count',
            'prison_count',
            'bank_transfer_details',
            'debit_card_details',
            'created',
            'modified',
            'monitoring',
        )


class PrisonerProfileSerializer(serializers.ModelSerializer):
    prisons = PrisonSerializer(many=True)
    current_prison = PrisonSerializer()
    provided_names = serializers.SerializerMethodField()

    # return None where this is a nested serializer
    sender_count = serializers.IntegerField(required=False)
    recipient_count = serializers.IntegerField(required=False)
    monitoring = serializers.BooleanField(required=False)

    class Meta:
        model = PrisonerProfile
        fields = (
            'id',
            'credit_count',
            'credit_total',
            'disbursement_count',
            'disbursement_total',
            'sender_count',
            'recipient_count',
            'prisoner_name',
            'prisoner_number',
            'prisoner_dob',
            'created',
            'modified',
            'prisons',
            'current_prison',
            'provided_names',
            'monitoring',
        )

    def get_provided_names(self, obj):
        return list(obj.provided_names.values_list('name', flat=True))


class BankTransferRecipientDetailsSerializer(serializers.ModelSerializer):
    recipient_sort_code = serializers.CharField(
        source='recipient_bank_account.sort_code'
    )
    recipient_account_number = serializers.CharField(
        source='recipient_bank_account.account_number'
    )
    recipient_roll_number = serializers.CharField(
        source='recipient_bank_account.roll_number'
    )

    class Meta:
        model = BankTransferRecipientDetails
        fields = (
            'recipient_sort_code',
            'recipient_account_number',
            'recipient_roll_number',
        )


class RecipientProfileSerializer(serializers.ModelSerializer):
    bank_transfer_details = BankTransferRecipientDetailsSerializer(many=True)

    # return None where this is a nested serializer
    prisoner_count = serializers.IntegerField(required=False)
    prison_count = serializers.IntegerField(required=False)
    monitoring = serializers.BooleanField(required=False)

    class Meta:
        model = RecipientProfile
        fields = (
            'id',
            'disbursement_count',
            'disbursement_total',
            'prisoner_count',
            'prison_count',
            'bank_transfer_details',
            'created',
            'modified',
            'monitoring',
        )


class SearchFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchFilter
        fields = ('field', 'value',)


class SavedSearchSerializer(serializers.ModelSerializer):
    filters = SearchFilterSerializer(many=True)
    last_result_count = serializers.IntegerField(required=False)
    site_url = serializers.CharField(required=False)

    class Meta:
        model = SavedSearch
        read_only_fields = ('id',)
        fields = (
            'id',
            'description',
            'endpoint',
            'last_result_count',
            'site_url',
            'filters',
        )

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        filters = validated_data.pop('filters', [])
        saved_search = super().create(validated_data)
        for searchfilter in filters:
            SearchFilter.objects.create(saved_search=saved_search, **searchfilter)
        return saved_search

    def update(self, instance, validated_data):
        filters = validated_data.pop('filters', [])
        instance.filters.all().delete()
        for searchfilter in filters:
            SearchFilter.objects.create(saved_search=instance, **searchfilter)
        return super().update(instance, validated_data)


class CheckAutoAcceptRuleStateSerializer(serializers.ModelSerializer):
    active = serializers.BooleanField(required=False)
    added_by = BasicUserSerializer(read_only=True)

    class Meta:
        model = CheckAutoAcceptRuleState
        fields = [
            'added_by',
            'active',
            'reason',
            'created',
            'auto_accept_rule'
        ]
        read_only_fields = (
            'id',
            'auto_accept_rule',
            'created',
        )

    def validate(self, attrs):
        if self.instance and attrs.get('active') is None:
            raise ValidationError({
                'active': ValidationError(_('On update, states[0].active must be specified'))
            })
        return super().validate(attrs)


class DebitCardSenderDetailsCardholderNamesSerializer(DebitCardSenderDetailsSerializer):
    cardholder_names = serializers.SerializerMethodField()
    sender = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = DebitCardSenderDetailsSerializer.Meta.model
        fields = DebitCardSenderDetailsSerializer.Meta.fields + ('cardholder_names', 'sender')

    def get_cardholder_names(self, instance):
        yield from (cardholder.name for cardholder in instance.cardholder_names.all())


class CheckAutoAcceptRuleSerializer(serializers.ModelSerializer):
    states = CheckAutoAcceptRuleStateSerializer(many=True, required=True)

    # List/Retrieve only
    debit_card_sender_details = DebitCardSenderDetailsCardholderNamesSerializer(read_only=True)
    prisoner_profile = PrisonerProfileSerializer(read_only=True)

    # Create/Update only
    debit_card_sender_details_id = serializers.PrimaryKeyRelatedField(
        queryset=DebitCardSenderDetails.objects.all(),
        write_only=True
    )
    prisoner_profile_id = serializers.PrimaryKeyRelatedField(
        queryset=PrisonerProfile.objects.all(),
        write_only=True
    )

    def is_valid(self, raise_exception=False):
        # We override is_valid to make this check before the built-in validators catch it, so we can add our own
        # error message as we want to match against it in logic within noms-ops, therefore want it to be in our control
        if self.instance is None and CheckAutoAcceptRule.objects.filter(
            debit_card_sender_details=self.initial_data.get('debit_card_sender_details_id'),
            prisoner_profile=self.initial_data.get('prisoner_profile_id')
        ).first():
            # This inner exception is intentionally not wrapped in gettext as we rely on it passing a check against
            # its value in noms-ops
            raise ValidationError({
                'non_field_errors': [
                    'An existing AutoAcceptRule is present for this DebitCardSenderDetails/PrisonerProfile pair'
                ]
            })
        return super().is_valid(raise_exception)

    def validate(self, attrs):
        if len(attrs['states']) != 1:
            raise ValidationError(
                _(f'When creating or updating an auto-accept rule, states must be of length 1, not {len(attrs.states)}')
            )
        return super().validate(attrs)

    def create(self, validated_data):
        auto_accept_rule = CheckAutoAcceptRule.objects.create(
            debit_card_sender_details=validated_data['debit_card_sender_details_id'],
            prisoner_profile=validated_data['prisoner_profile_id'],
        )
        CheckAutoAcceptRuleStateSerializer().create(
            validated_data={
                'active': True,
                'reason': validated_data['states'][0]['reason'],
                'added_by': self.context['request'].user,
                'auto_accept_rule': auto_accept_rule
            }
        )
        auto_accept_rule.refresh_from_db()
        return auto_accept_rule

    def update(self, instance, validated_data):
        # The only operation we support here is to create a new associated state
        instance.states.add(
            CheckAutoAcceptRuleStateSerializer().create(
                validated_data={
                    'active': validated_data['states'][0]['active'],
                    'reason': validated_data['states'][0]['reason'],
                    'added_by': self.context['request'].user,
                    'auto_accept_rule': instance
                }
            )
        )
        instance.save()
        return instance

    class Meta:
        model = CheckAutoAcceptRule
        fields = [
            'id',
            'created',
            'debit_card_sender_details',
            'prisoner_profile',
            'states',
            'debit_card_sender_details_id',
            'prisoner_profile_id',
        ]
        read_only_fields = [
            'id',
            'created',
            'debit_card_sender_details',
            'prisoner_profile',
        ]
        write_only_fields = [
            'debit_card_sender_details_id',
            'prisoner_profile_id',
        ]


class CheckSerializer(serializers.ModelSerializer):
    actioned_by_name = serializers.SerializerMethodField('get_actioned_by_name_from_user')
    assigned_to_name = serializers.SerializerMethodField('get_assigned_to_name_from_user')
    auto_accept_rule_state = CheckAutoAcceptRuleStateSerializer(read_only=True, required=False)

    class Meta:
        model = Check
        fields = (
            'id',
            'credit',
            'status',
            'description',
            'rules',
            'actioned_at',
            'actioned_by',
            'assigned_to',
            'decision_reason',
            'actioned_by_name',
            'assigned_to_name',
            'rejection_reasons',
            'auto_accept_rule_state',
        )
        read_only_fields = (
            'id',
            'credit',
            'status',
            'description',
            'rules',
            'actioned_at',
            'actioned_by',
            'decision_reason',
        )

    def get_actioned_by_name_from_user(self, check):
        if check.actioned_by is not None:
            actioned_by_name = check.actioned_by.get_full_name()
            return actioned_by_name
        else:
            return None

    def get_assigned_to_name_from_user(self, check):
        if check.assigned_to is not None:
            assigned_to_name = check.assigned_to.get_full_name()
            return assigned_to_name
        else:
            return None

    def update(self, instance, validated_data):
        if instance.assigned_to_id and validated_data.get('assigned_to') not in (None, instance.assigned_to_id):
            raise ValidationError(
                'That check is already assigned to {}'.format(instance.assigned_to.get_full_name())
            )
        return super().update(instance, validated_data)


class CheckCreditSerializer(CheckSerializer):
    from credit.serializers import SecurityCreditSerializer

    credit = SecurityCreditSerializer(many=False)

    class Meta:
        model = Check
        fields = CheckSerializer.Meta.fields + (
            'credit',
        )
        read_only_fields = CheckSerializer.Meta.read_only_fields


class AcceptCheckSerializer(CheckCreditSerializer):
    decision_reason = serializers.CharField(required=True, allow_blank=True)

    class Meta:
        model = Check
        fields = ('decision_reason', 'rejection_reasons')
        read_only_fields = (
            'id',
            'credit',
            'description',
            'rules'
        )

    def validate(self, data):
        if data.get('rejection_reasons'):
            raise serializers.ValidationError('You cannot give rejection reasons when accepting a check')
        return super().validate(data)

    def accept(self, by):
        try:
            self.instance.accept(
                by,
                self.validated_data['decision_reason'],
            )
        except DjangoValidationError as e:
            raise ValidationError(
                detail=e.message_dict,
            )


class RejectCheckSerializer(CheckCreditSerializer):
    decision_reason = serializers.CharField(required=True, allow_blank=True)
    rejection_reasons = serializers.JSONField(required=True)

    class Meta:
        model = Check
        fields = (
            'decision_reason',
            'rejection_reasons'
        )
        read_only_fields = (
            'id',
            'credit',
            'description',
            'rules'
        )

    def validate_rejection_reasons(self, data):
        if not data:
            raise serializers.ValidationError('This field cannot be blank.')
        return data

    def reject(self, by):
        try:
            self.instance.reject(
                by,
                self.validated_data['decision_reason'],
                self.validated_data['rejection_reasons'],
            )
        except DjangoValidationError as e:
            raise ValidationError(
                detail=e.message_dict,
            )
