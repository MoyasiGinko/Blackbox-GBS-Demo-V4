from rest_framework import serializers
from django.utils import timezone
from .models import Payment
from subscription_app.models import SubscriptionPlan
from auth_app.models import User

class PaymentSerializer(serializers.ModelSerializer):
    """Basic payment serializer for listing."""
    user_email = serializers.CharField(source='user.email', read_only=True)
    subscription_plan_name = serializers.CharField(source='subscription_plan.name', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'user_email', 'subscription_plan_name', 'amount',
            'payment_status', 'payment_method', 'transaction_id',
            'payment_date', 'payment_metadata'
        ]

class PaymentDetailSerializer(serializers.ModelSerializer):
    """Detailed payment serializer with related data."""
    user = serializers.SerializerMethodField()
    subscription_plan = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'subscription_plan', 'amount', 'payment_status',
            'payment_method', 'transaction_id', 'payment_date', 'payment_metadata'
        ]

    def get_user(self, obj):
        return {
            'id': str(obj.user.id),
            'email': obj.user.email,
            'full_name': obj.user.full_name
        }

    def get_subscription_plan(self, obj):
        return {
            'id': str(obj.subscription_plan.id),
            'name': obj.subscription_plan.name,
            'price': obj.subscription_plan.price,
            'duration_days': obj.subscription_plan.duration_days
        }

class CreatePaymentSerializer(serializers.Serializer):
    """Serializer for creating a new payment."""
    subscription_plan_id = serializers.UUIDField(required=True)
    payment_method = serializers.ChoiceField(
        choices=Payment.METHOD_CHOICES,
        default='stripe'
    )

    def validate_subscription_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive subscription plan.")

class ProcessPaymentSerializer(serializers.Serializer):
    """Serializer for processing payment through external gateways."""
    payment_id = serializers.UUIDField(required=True)
    external_transaction_id = serializers.CharField(max_length=255, required=False)
    payment_status = serializers.ChoiceField(
        choices=[('success', 'Success'), ('failed', 'Failed')],
        required=True
    )
    gateway_response = serializers.JSONField(required=False, default=dict)

    def validate_payment_id(self, value):
        try:
            payment = Payment.objects.get(id=value, payment_status='pending')
            return value
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found or not in pending status.")

class RefundPaymentSerializer(serializers.Serializer):
    """Serializer for processing payment refunds."""
    payment_id = serializers.UUIDField(required=True)
    refund_reason = serializers.CharField(max_length=500, required=False)
    refund_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        help_text="Partial refund amount. Leave empty for full refund."
    )

    def validate_payment_id(self, value):
        try:
            payment = Payment.objects.get(id=value, payment_status='success')
            return value
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found or not eligible for refund.")

class PaymentStatsSerializer(serializers.Serializer):
    """Serializer for payment statistics."""
    total_payments = serializers.IntegerField()
    successful_payments = serializers.IntegerField()
    failed_payments = serializers.IntegerField()
    pending_payments = serializers.IntegerField()
    refunded_payments = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    refunded_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    success_rate = serializers.FloatField()
    payments_by_method = serializers.DictField()
    revenue_by_month = serializers.ListField()

class UserPaymentHistorySerializer(serializers.ModelSerializer):
    """User payment history serializer."""
    subscription_plan_name = serializers.CharField(source='subscription_plan.name', read_only=True)
    days_since_payment = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'subscription_plan_name', 'amount', 'payment_status',
            'payment_method', 'payment_date', 'days_since_payment'
        ]

    def get_days_since_payment(self, obj):
        delta = timezone.now() - obj.payment_date
        return delta.days
