from rest_framework import serializers
from django.utils import timezone
from .models import SubscriptionPlan, UserSubscription
from service_app.serializers import ServiceSerializer
from payment_app.serializers import PaymentSerializer

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Basic subscription plan serializer for listing."""
    service_count = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'description', 'price', 'duration_days',
            'max_services', 'service_count', 'is_active', 'created_at'
        ]

    def get_service_count(self, obj):
        return obj.services.filter(is_active=True).count()

class SubscriptionPlanDetailSerializer(serializers.ModelSerializer):
    """Detailed subscription plan serializer with services."""
    services = ServiceSerializer(many=True, read_only=True)
    service_count = serializers.SerializerMethodField()
    subscriber_count = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'description', 'price', 'duration_days',
            'max_services', 'services', 'service_count', 'subscriber_count',
            'is_active', 'created_at'
        ]

    def get_service_count(self, obj):
        return obj.services.filter(is_active=True).count()

    def get_subscriber_count(self, obj):
        return obj.usersubscription_set.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).count()

class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Basic user subscription serializer."""
    subscription_name = serializers.CharField(source='subscription.name', read_only=True)
    subscription_price = serializers.DecimalField(source='subscription.price', max_digits=8, decimal_places=2, read_only=True)
    is_expired = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = [
            'id', 'subscription_name', 'subscription_price', 'is_active',
            'purchased_at', 'expires_at', 'is_expired', 'days_remaining'
        ]

    def get_is_expired(self, obj):
        return obj.is_expired()

    def get_days_remaining(self, obj):
        if obj.is_expired():
            return 0
        delta = obj.expires_at - timezone.now()
        return max(0, delta.days)

class UserSubscriptionDetailSerializer(serializers.ModelSerializer):
    """Detailed user subscription serializer with related data."""
    subscription = SubscriptionPlanSerializer(read_only=True)
    selected_services = ServiceSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)
    is_expired = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    accessible_services_count = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = [
            'id', 'subscription', 'selected_services', 'payment',
            'is_active', 'purchased_at', 'expires_at', 'is_expired',
            'days_remaining', 'accessible_services_count'
        ]

    def get_is_expired(self, obj):
        return obj.is_expired()

    def get_days_remaining(self, obj):
        if obj.is_expired():
            return 0
        delta = obj.expires_at - timezone.now()
        return max(0, delta.days)

    def get_accessible_services_count(self, obj):
        if obj.selected_services.exists():
            return obj.selected_services.filter(is_active=True).count()
        return obj.subscription.services.filter(is_active=True).count()

class AdminUserSubscriptionDetailSerializer(serializers.ModelSerializer):
    """Admin detailed user subscription serializer with user data."""
    subscription = SubscriptionPlanSerializer(read_only=True)
    selected_services = ServiceSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    is_expired = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    accessible_services_count = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = [
            'id', 'user_email', 'user_full_name', 'subscription', 'selected_services', 'payment',
            'is_active', 'purchased_at', 'expires_at', 'is_expired',
            'days_remaining', 'accessible_services_count'
        ]

    def get_is_expired(self, obj):
        return obj.is_expired()

    def get_days_remaining(self, obj):
        if obj.is_expired():
            return 0
        delta = obj.expires_at - timezone.now()
        return max(0, delta.days)

    def get_accessible_services_count(self, obj):
        if obj.selected_services.exists():
            return obj.selected_services.filter(is_active=True).count()
        return obj.subscription.services.filter(is_active=True).count()

class PurchaseSubscriptionSerializer(serializers.Serializer):
    """Serializer for purchasing a subscription."""
    subscription_plan_id = serializers.UUIDField(required=True)
    selected_services = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        help_text="List of service IDs to include in subscription (optional for plans that allow selection)"
    )
    payment_method = serializers.ChoiceField(
        choices=[('stripe', 'Stripe'), ('paypal', 'PayPal'), ('crypto', 'Cryptocurrency')],
        default='stripe'
    )

    def validate_subscription_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive subscription plan.")

    def validate(self, data):
        plan_id = data.get('subscription_plan_id')
        selected_services = data.get('selected_services', [])

        if plan_id and selected_services:
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id)
                if len(selected_services) > plan.max_services:
                    raise serializers.ValidationError(
                        f"You can only select up to {plan.max_services} services for this plan."
                    )
            except SubscriptionPlan.DoesNotExist:
                pass  # This will be caught by the field validator

        return data

class UpdateSubscriptionServicesSerializer(serializers.Serializer):
    """Serializer for updating selected services in a subscription."""
    selected_services = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        help_text="List of service IDs to include in subscription"
    )
