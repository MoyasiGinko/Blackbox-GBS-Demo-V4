from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from django.db.models.functions import TruncMonth
from datetime import timedelta
from .models import Payment
from .serializers import (
    PaymentSerializer,
    PaymentDetailSerializer,
    CreatePaymentSerializer,
    ProcessPaymentSerializer,
    RefundPaymentSerializer,
    PaymentStatsSerializer,
    UserPaymentHistorySerializer
)
from subscription_app.models import SubscriptionPlan, UserSubscription

# ==== USER ENDPOINTS ====

class CreatePaymentView(generics.CreateAPIView):
    """
    Create a new payment record.
    This would typically be called before redirecting to payment gateway.
    """
    serializer_class = CreatePaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Get subscription plan
            plan_id = serializer.validated_data['subscription_plan_id']
            payment_method = serializer.validated_data['payment_method']

            try:
                plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                return Response(
                    {"error": "Subscription plan not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Create payment record
            payment = Payment.objects.create(
                user=request.user,
                subscription_plan=plan,
                amount=plan.price,
                payment_method=payment_method,
                payment_status='pending',
                transaction_id=f"temp_{timezone.now().timestamp()}"  # Temporary ID
            )

            response_serializer = PaymentDetailSerializer(payment)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProcessPaymentView(APIView):
    """
    Process payment confirmation from external gateway.
    Updates payment status based on gateway response.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ProcessPaymentSerializer(data=request.data)
        if serializer.is_valid():
            payment_id = serializer.validated_data['payment_id']
            external_transaction_id = serializer.validated_data.get('external_transaction_id')
            payment_status = serializer.validated_data['payment_status']
            gateway_response = serializer.validated_data.get('gateway_response', {})

            try:
                payment = Payment.objects.get(
                    id=payment_id,
                    user=request.user,
                    payment_status='pending'
                )
            except Payment.DoesNotExist:
                return Response(
                    {"error": "Payment not found or not in pending status."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Update payment
            payment.payment_status = payment_status
            if external_transaction_id:
                payment.transaction_id = external_transaction_id
            payment.payment_metadata.update({
                'gateway_response': gateway_response,
                'processed_at': timezone.now().isoformat()
            })
            payment.save()

            # If payment successful, create subscription
            if payment_status == 'success':
                expires_at = timezone.now() + timedelta(days=payment.subscription_plan.duration_days)
                UserSubscription.objects.create(
                    user=payment.user,
                    subscription=payment.subscription_plan,
                    payment=payment,
                    expires_at=expires_at
                )

            response_serializer = PaymentDetailSerializer(payment)
            return Response({
                "message": f"Payment {payment_status}",
                "payment": response_serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserPaymentHistoryView(generics.ListAPIView):
    """
    Get user's payment history.
    """
    serializer_class = UserPaymentHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Payment.objects.filter(user=self.request.user).order_by('-payment_date')

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(payment_status=status_filter)

        # Filter by payment method
        method_filter = self.request.query_params.get('method')
        if method_filter:
            queryset = queryset.filter(payment_method=method_filter)

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)

        return queryset

class UserPaymentDetailView(generics.RetrieveAPIView):
    """
    Get detailed information about a specific payment.
    """
    serializer_class = PaymentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

class UserPaymentStatsView(APIView):
    """
    Get user's payment statistics.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_payments = Payment.objects.filter(user=request.user)

        stats = {
            'total_payments': user_payments.count(),
            'successful_payments': user_payments.filter(payment_status='success').count(),
            'failed_payments': user_payments.filter(payment_status='failed').count(),
            'pending_payments': user_payments.filter(payment_status='pending').count(),
            'total_spent': user_payments.filter(payment_status='success').aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'favorite_payment_method': self._get_favorite_payment_method(user_payments),
            'last_payment': self._get_last_payment(user_payments),
            'monthly_spending': self._get_monthly_spending(user_payments)
        }

        return Response(stats, status=status.HTTP_200_OK)

    def _get_favorite_payment_method(self, payments):
        """Get user's most used payment method."""
        method_counts = payments.values('payment_method').annotate(
            count=Count('payment_method')
        ).order_by('-count').first()
        return method_counts['payment_method'] if method_counts else None

    def _get_last_payment(self, payments):
        """Get user's last payment."""
        last_payment = payments.order_by('-payment_date').first()
        if last_payment:
            return {
                'amount': last_payment.amount,
                'date': last_payment.payment_date,
                'status': last_payment.payment_status,
                'plan': last_payment.subscription_plan.name
            }
        return None

    def _get_monthly_spending(self, payments):
        """Get user's spending by month for the last 6 months."""
        six_months_ago = timezone.now() - timedelta(days=180)
        monthly_data = payments.filter(
            payment_status='success',
            payment_date__gte=six_months_ago
        ).annotate(
            month=TruncMonth('payment_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')

        return [
            {
                'month': item['month'].strftime('%Y-%m'),
                'amount': float(item['total'])
            }
            for item in monthly_data
        ]

# ==== ADMIN ENDPOINTS ====

class AdminPaymentListView(generics.ListAPIView):
    """
    Admin endpoint to view all payments with filtering.
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        queryset = Payment.objects.all().select_related('user', 'subscription_plan').order_by('-payment_date')

        # Filter by user
        user_email = self.request.query_params.get('user_email')
        if user_email:
            queryset = queryset.filter(user__email__icontains=user_email)

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(payment_status=status_filter)

        # Filter by payment method
        method_filter = self.request.query_params.get('method')
        if method_filter:
            queryset = queryset.filter(payment_method=method_filter)

        # Filter by subscription plan
        plan_id = self.request.query_params.get('plan_id')
        if plan_id:
            queryset = queryset.filter(subscription_plan_id=plan_id)

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)

        # Filter by amount range
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(amount__lte=max_amount)

        return queryset

class AdminPaymentDetailView(generics.RetrieveAPIView):
    """
    Admin endpoint to view detailed payment information.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentDetailSerializer
    permission_classes = [permissions.IsAdminUser]

class AdminRefundPaymentView(APIView):
    """
    Admin endpoint to process payment refunds.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = RefundPaymentSerializer(data=request.data)
        if serializer.is_valid():
            payment_id = serializer.validated_data['payment_id']
            refund_reason = serializer.validated_data.get('refund_reason', '')
            refund_amount = serializer.validated_data.get('refund_amount')

            try:
                payment = Payment.objects.get(id=payment_id, payment_status='success')
            except Payment.DoesNotExist:
                return Response(
                    {"error": "Payment not found or not eligible for refund."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Process refund (in real app, this would call payment gateway)
            refund_amount = refund_amount or payment.amount

            # Update payment status
            payment.payment_status = 'refunded'
            payment.payment_metadata.update({
                'refund_reason': refund_reason,
                'refund_amount': str(refund_amount),
                'refunded_at': timezone.now().isoformat(),
                'refunded_by': str(request.user.id)
            })
            payment.save()

            # Deactivate associated subscription
            try:
                subscription = UserSubscription.objects.get(payment=payment)
                subscription.is_active = False
                subscription.save()
            except UserSubscription.DoesNotExist:
                pass

            response_serializer = PaymentDetailSerializer(payment)
            return Response({
                "message": f"Payment refunded successfully. Amount: ${refund_amount}",
                "payment": response_serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminPaymentStatsView(APIView):
    """
    Admin endpoint to get comprehensive payment statistics.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        # Get time range from query params
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)

        all_payments = Payment.objects.all()
        recent_payments = Payment.objects.filter(payment_date__gte=start_date)

        stats = {
            'total_payments': all_payments.count(),
            'successful_payments': all_payments.filter(payment_status='success').count(),
            'failed_payments': all_payments.filter(payment_status='failed').count(),
            'pending_payments': all_payments.filter(payment_status='pending').count(),
            'refunded_payments': all_payments.filter(payment_status='refunded').count(),
            'total_revenue': all_payments.filter(payment_status='success').aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'refunded_amount': all_payments.filter(payment_status='refunded').aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'success_rate': self._calculate_success_rate(all_payments),
            'payments_by_method': self._get_payments_by_method(all_payments),
            'revenue_by_month': self._get_revenue_by_month(),
            'recent_stats': {
                f'last_{days}_days': {
                    'payments': recent_payments.count(),
                    'revenue': recent_payments.filter(payment_status='success').aggregate(
                        total=Sum('amount')
                    )['total'] or 0,
                    'average_amount': recent_payments.filter(payment_status='success').aggregate(
                        avg=Avg('amount')
                    )['avg'] or 0
                }
            },
            'top_plans': self._get_top_subscription_plans(),
            'payment_trends': self._get_payment_trends()
        }

        return Response(stats, status=status.HTTP_200_OK)

    def _calculate_success_rate(self, payments):
        """Calculate payment success rate."""
        total = payments.exclude(payment_status='pending').count()
        if total == 0:
            return 0
        successful = payments.filter(payment_status='success').count()
        return round((successful / total) * 100, 2)

    def _get_payments_by_method(self, payments):
        """Get payment count by method."""
        methods = payments.values('payment_method').annotate(
            count=Count('payment_method'),
            revenue=Sum('amount', filter=Q(payment_status='success'))
        )
        return {
            method['payment_method']: {
                'count': method['count'],
                'revenue': float(method['revenue'] or 0)
            }
            for method in methods
        }

    def _get_revenue_by_month(self):
        """Get revenue by month for the last 12 months."""
        twelve_months_ago = timezone.now() - timedelta(days=365)
        monthly_data = Payment.objects.filter(
            payment_status='success',
            payment_date__gte=twelve_months_ago
        ).annotate(
            month=TruncMonth('payment_date')
        ).values('month').annotate(
            revenue=Sum('amount'),
            count=Count('id')
        ).order_by('month')

        return [
            {
                'month': item['month'].strftime('%Y-%m'),
                'revenue': float(item['revenue']),
                'count': item['count']
            }
            for item in monthly_data
        ]

    def _get_top_subscription_plans(self):
        """Get top subscription plans by revenue."""
        plans = Payment.objects.filter(
            payment_status='success'
        ).values(
            'subscription_plan__name',
            'subscription_plan__price'
        ).annotate(
            revenue=Sum('amount'),
            count=Count('id')
        ).order_by('-revenue')[:5]

        return [
            {
                'plan_name': plan['subscription_plan__name'],
                'price': float(plan['subscription_plan__price']),
                'revenue': float(plan['revenue']),
                'sales_count': plan['count']
            }
            for plan in plans
        ]

    def _get_payment_trends(self):
        """Get payment trends for the last 7 days."""
        seven_days_ago = timezone.now() - timedelta(days=7)
        daily_data = Payment.objects.filter(
            payment_date__gte=seven_days_ago
        ).extra(
            select={'day': 'date(payment_date)'}
        ).values('day').annotate(
            total_payments=Count('id'),
            successful_payments=Count('id', filter=Q(payment_status='success')),
            revenue=Sum('amount', filter=Q(payment_status='success'))
        ).order_by('day')

        return [
            {
                'date': item['day'],
                'total_payments': item['total_payments'],
                'successful_payments': item['successful_payments'],
                'revenue': float(item['revenue'] or 0)
            }
            for item in daily_data
        ]
