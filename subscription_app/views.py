from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from .models import SubscriptionPlan, UserSubscription
from .serializers_v2 import (    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    SubscriptionPlanDetailSerializer,
    UserSubscriptionDetailSerializer,
    AdminUserSubscriptionDetailSerializer,
    PurchaseSubscriptionSerializer
)
from payment_app.models import Payment
from service_app.models import Service

# ==== USER ENDPOINTS ====

class SubscriptionPlanListView(generics.ListAPIView):
    """
    List all available subscription plans for users to browse.
    """
    queryset = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

class SubscriptionPlanDetailView(generics.RetrieveAPIView):
    """
    Get detailed information about a specific subscription plan.
    """
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserSubscriptionListView(generics.ListAPIView):
    """
    List user's current and past subscriptions.
    """
    serializer_class = UserSubscriptionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return UserSubscription.objects.filter(user=user).order_by('-purchased_at')

class UserActiveSubscriptionsView(generics.ListAPIView):
    """
    List user's currently active subscriptions only.
    """
    serializer_class = UserSubscriptionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return UserSubscription.objects.filter(
            user=user,
            is_active=True,
            expires_at__gt=timezone.now()
        ).order_by('-purchased_at')

class PurchaseSubscriptionView(APIView):
    """
    Purchase a subscription plan.
    Creates payment record and user subscription upon successful payment.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PurchaseSubscriptionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        plan_id = serializer.validated_data['subscription_plan_id']
        selected_service_ids = serializer.validated_data.get('selected_services', [])
        payment_method = serializer.validated_data.get('payment_method', 'stripe')

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({"error": "Subscription plan not found."}, status=status.HTTP_404_NOT_FOUND)

        # Validate selected services
        if selected_service_ids:
            if len(selected_service_ids) > plan.max_services:
                return Response({
                    "error": f"You can only select up to {plan.max_services} services for this plan."
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if all selected services are available in the plan
            plan_service_ids = set(plan.services.values_list('id', flat=True))
            selected_service_ids_set = set(selected_service_ids)

            if not selected_service_ids_set.issubset(plan_service_ids):
                return Response({
                    "error": "Some selected services are not available in this plan."
                }, status=status.HTTP_400_BAD_REQUEST)

        # Create payment record
        payment = Payment.objects.create(
            user=user,
            subscription_plan=plan,
            amount=plan.price,
            payment_method=payment_method,
            payment_status='success',  # In real app, this would be pending until payment gateway confirms
            transaction_id=f"txn_{timezone.now().timestamp()}"  # Mock transaction ID
        )

        # Create user subscription
        expires_at = timezone.now() + timedelta(days=plan.duration_days)
        user_subscription = UserSubscription.objects.create(
            user=user,
            subscription=plan,
            payment=payment,
            expires_at=expires_at
        )

        # Set selected services if provided
        if selected_service_ids:
            selected_services = Service.objects.filter(id__in=selected_service_ids)
            user_subscription.selected_services.set(selected_services)

        response_serializer = UserSubscriptionDetailSerializer(user_subscription)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class UpdateSubscriptionServicesView(APIView):
    """
    Update selected services for a user's subscription.
    Only works for plans that allow service selection.
    """
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, subscription_id):
        try:
            subscription = UserSubscription.objects.get(
                id=subscription_id,
                user=request.user,
                is_active=True,
                expires_at__gt=timezone.now()
            )
        except UserSubscription.DoesNotExist:
            return Response({"error": "Active subscription not found."}, status=status.HTTP_404_NOT_FOUND)

        selected_service_ids = request.data.get('selected_services', [])

        if len(selected_service_ids) > subscription.subscription.max_services:
            return Response({
                "error": f"You can only select up to {subscription.subscription.max_services} services for this plan."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate services are available in the plan
        plan_service_ids = set(subscription.subscription.services.values_list('id', flat=True))
        selected_service_ids_set = set(selected_service_ids)

        if not selected_service_ids_set.issubset(plan_service_ids):
            return Response({
                "error": "Some selected services are not available in this plan."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update selected services
        selected_services = Service.objects.filter(id__in=selected_service_ids)
        subscription.selected_services.set(selected_services)

        response_serializer = UserSubscriptionDetailSerializer(subscription)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

class CancelSubscriptionView(APIView):
    """
    Cancel a user's subscription.
    Sets is_active to False but keeps the record for history.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, subscription_id):
        try:
            subscription = UserSubscription.objects.get(
                id=subscription_id,
                user=request.user,
                is_active=True
            )
        except UserSubscription.DoesNotExist:
            return Response({"error": "Active subscription not found."}, status=status.HTTP_404_NOT_FOUND)

        subscription.is_active = False
        subscription.save()

        return Response({
            "detail": "Subscription cancelled successfully.",
            "subscription_id": str(subscription.id)
        }, status=status.HTTP_200_OK)

class SubscriptionStatsView(APIView):
    """
    Get user's subscription statistics and summary.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get subscription statistics
        total_subscriptions = UserSubscription.objects.filter(user=user).count()
        active_subscriptions = UserSubscription.objects.filter(
            user=user,
            is_active=True,
            expires_at__gt=timezone.now()
        ).count()

        # Get accessible services count
        accessible_services = user.get_accessible_services() if hasattr(user, 'get_accessible_services') else []

        stats = {
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'accessible_services_count': len(accessible_services),
            'total_spent': sum(
                sub.payment.amount for sub in UserSubscription.objects.filter(user=user)
                if sub.payment.payment_status == 'success'
            )
        }

        return Response(stats, status=status.HTTP_200_OK)

# ==== ADMIN ENDPOINTS ====

class AdminSubscriptionPlanListCreateView(generics.ListCreateAPIView):
    """
    Admin endpoint to list and create subscription plans.
    """
    queryset = SubscriptionPlan.objects.all().order_by('price')
    serializer_class = SubscriptionPlanDetailSerializer
    permission_classes = [permissions.IsAdminUser]

class AdminSubscriptionPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin endpoint to retrieve, update, or delete a subscription plan.
    """
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanDetailSerializer
    permission_classes = [permissions.IsAdminUser]

class AdminUserSubscriptionListView(generics.ListAPIView):
    """
    Admin endpoint to view all user subscriptions with filtering.
    """
    serializer_class = AdminUserSubscriptionDetailSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        queryset = UserSubscription.objects.all().select_related('user', 'subscription', 'payment')

        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter by plan
        plan_id = self.request.query_params.get('plan_id')
        if plan_id:
            queryset = queryset.filter(subscription_id=plan_id)

        # Filter by status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by expiry status
        expired = self.request.query_params.get('expired')
        if expired is not None:
            if expired.lower() == 'true':
                queryset = queryset.filter(expires_at__lt=timezone.now())
            else:
                queryset = queryset.filter(expires_at__gte=timezone.now())

        return queryset.order_by('-purchased_at')

class AdminSubscriptionStatsView(APIView):
    """
    Admin endpoint to get subscription statistics and analytics.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        stats = {
            'total_plans': SubscriptionPlan.objects.count(),
            'active_plans': SubscriptionPlan.objects.filter(is_active=True).count(),
            'total_subscriptions': UserSubscription.objects.count(),
            'active_subscriptions': UserSubscription.objects.filter(
                is_active=True,
                expires_at__gt=timezone.now()
            ).count(),
            'expired_subscriptions': UserSubscription.objects.filter(
                expires_at__lt=timezone.now()
            ).count(),
            'total_revenue': sum(
                payment.amount for payment in Payment.objects.filter(payment_status='success')
            ),
            'plans_by_popularity': self._get_plans_by_popularity(),
            'recent_subscriptions': self._get_recent_subscriptions()
        }

        return Response(stats, status=status.HTTP_200_OK)

    def _get_plans_by_popularity(self):
        """Get subscription plans ordered by popularity (number of purchases)."""
        plans = SubscriptionPlan.objects.annotate(
            purchase_count=Count('usersubscription')
        ).order_by('-purchase_count')[:5]

        return [
            {
                'plan_name': plan.name,
                'purchase_count': plan.purchase_count,
                'price': plan.price
            }
            for plan in plans
        ]

    def _get_recent_subscriptions(self):
        """Get recent subscriptions for dashboard."""
        recent = UserSubscription.objects.select_related('user', 'subscription').order_by('-purchased_at')[:10]

        return [
            {
                'user_email': sub.user.email,
                'plan_name': sub.subscription.name,
                'purchased_at': sub.purchased_at,
                'expires_at': sub.expires_at,
                'is_active': sub.is_active and sub.expires_at > timezone.now()
            }
            for sub in recent
        ]
