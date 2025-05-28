from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.db.models.functions import TruncDate
from datetime import timedelta
from .models import LoginService, Cookie, UserService, CookieInjectionLog, CookieExtractionJob
from .serializers import (
    LoginServiceSerializer,
    CreateLoginServiceSerializer,
    LoginServiceDetailSerializer,
    UserServiceSerializer,
    CreateUserServiceRequestSerializer,
    UserServiceDetailSerializer,
    CookieSerializer,
    CookieDataSerializer,
    CreateCookieSerializer,
    CookieInjectionLogSerializer,
    CookieExtractionJobSerializer,
    CreateExtractionJobSerializer,
    CookieStatsSerializer
)
from subscription_app.models import UserSubscription

# ===== USER ENDPOINTS =====

class RequestServiceAccessView(generics.CreateAPIView):
    """
    User endpoint to request access to a service.
    Creates a UserService request that needs admin approval.
    """
    serializer_class = CreateUserServiceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user_service = serializer.save()
            response_serializer = UserServiceSerializer(user_service)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserAccessibleServicesView(generics.ListAPIView):
    """
    List services the user has access to through active subscriptions.
    """
    serializer_class = UserServiceDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserService.objects.filter(
            user=self.request.user,
            status='active'
        ).order_by('-assigned_at')

class GetServiceCookieView(APIView):
    """
    Get cookie data for a service the user has access to.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, service_id):
        try:
            # Check if user has active access to this service
            user_service = UserService.objects.get(
                user=request.user,
                service_id=service_id,
                status='active'
            )
        except UserService.DoesNotExist:
            return Response(
                {"error": "No active access to this service"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get the most recent valid cookie
        cookie = user_service.cookies.filter(
            status='valid',
            expires_at__gt=timezone.now()
        ).order_by('-extracted_at').first()

        if not cookie:
            return Response(
                {"error": "No valid cookies available. Please try again later."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Record access
        user_service.record_access()

        # Log the injection
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')

        CookieInjectionLog.objects.create(
            cookie=cookie,
            user=request.user,
            injection_status='success',
            message=f"Cookie provided for {user_service.service.name}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        serializer = CookieDataSerializer(cookie)
        return Response(serializer.data)

class UserServiceHistoryView(generics.ListAPIView):
    """
    Get user's service access history and usage stats.
    """
    serializer_class = UserServiceDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserService.objects.filter(user=self.request.user).order_by('-assigned_at')

class UserCookieActivityView(generics.ListAPIView):
    """
    Get user's cookie injection activity logs.
    """
    serializer_class = CookieInjectionLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CookieInjectionLog.objects.filter(
            user=self.request.user
        ).order_by('-timestamp')[:50]  # Last 50 activities

# ===== ADMIN ENDPOINTS =====

class AdminLoginServiceListView(generics.ListCreateAPIView):
    """
    Admin endpoint to list and create login services.
    """
    queryset = LoginService.objects.all().order_by('-created_at')
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateLoginServiceSerializer
        return LoginServiceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        service_id = self.request.query_params.get('service_id')
        is_active = self.request.query_params.get('is_active')

        if service_id:
            queryset = queryset.filter(service_id=service_id)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

class AdminLoginServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin endpoint to retrieve, update, or delete a login service.
    """
    queryset = LoginService.objects.all()
    serializer_class = LoginServiceDetailSerializer
    permission_classes = [permissions.IsAdminUser]

class AdminPendingRequestsView(generics.ListAPIView):
    """
    Admin endpoint to list all pending user service requests.
    """
    serializer_class = UserServiceDetailSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return UserService.objects.filter(status='pending').order_by('-assigned_at')

class AdminApproveServiceRequestView(APIView):
    """
    Admin endpoint to approve a user service request.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_service_id):
        try:
            user_service = UserService.objects.get(id=user_service_id, status='pending')
        except UserService.DoesNotExist:
            return Response(
                {"error": "Pending request not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            success = user_service.activate()
            if success:
                serializer = UserServiceDetailSerializer(user_service)
                return Response({
                    "message": "Service access approved successfully",
                    "user_service": serializer.data
                })
            else:
                return Response(
                    {"error": "Service is already active"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class AdminRejectServiceRequestView(APIView):
    """
    Admin endpoint to reject a user service request.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_service_id):
        try:
            user_service = UserService.objects.get(id=user_service_id, status='pending')
            user_service.delete()
            return Response({"message": "Service request rejected and removed"})
        except UserService.DoesNotExist:
            return Response(
                {"error": "Pending request not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class AdminUserServicesView(generics.ListAPIView):
    """
    Admin endpoint to list all user services with filtering.
    """
    serializer_class = UserServiceDetailSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        queryset = UserService.objects.all().order_by('-assigned_at')

        # Filtering parameters
        user_id = self.request.query_params.get('user_id')
        service_id = self.request.query_params.get('service_id')
        status = self.request.query_params.get('status')

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if service_id:
            queryset = queryset.filter(service_id=service_id)
        if status:
            queryset = queryset.filter(status=status)

        return queryset

class AdminCookieListView(generics.ListCreateAPIView):
    """
    Admin endpoint to list and manually create cookies.
    """
    queryset = Cookie.objects.all().order_by('-extracted_at')
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateCookieSerializer
        return CookieSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        service_id = self.request.query_params.get('service_id')
        status = self.request.query_params.get('status')
        user_id = self.request.query_params.get('user_id')

        if service_id:
            queryset = queryset.filter(user_service__service_id=service_id)
        if status:
            queryset = queryset.filter(status=status)
        if user_id:
            queryset = queryset.filter(user_service__user_id=user_id)

        return queryset

class AdminCookieDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin endpoint to manage individual cookies.
    """
    queryset = Cookie.objects.all()
    serializer_class = CookieSerializer
    permission_classes = [permissions.IsAdminUser]

class AdminTriggerCookieExtractionView(APIView):
    """
    Admin endpoint to trigger cookie extraction for a login service.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = CreateExtractionJobSerializer(data=request.data)
        if serializer.is_valid():
            login_service_id = serializer.validated_data['login_service_id']

            # Create extraction job
            job = CookieExtractionJob.objects.create(
                login_service_id=login_service_id,
                status='pending'
            )

            # Here you would trigger the actual extraction task
            # For now, we'll just mark it as in progress
            job.status = 'in_progress'
            job.started_at = timezone.now()
            job.save()

            response_serializer = CookieExtractionJobSerializer(job)
            return Response({
                "message": "Cookie extraction job created",
                "job": response_serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminExtractionJobsView(generics.ListAPIView):
    """
    Admin endpoint to list cookie extraction jobs.
    """
    queryset = CookieExtractionJob.objects.all().order_by('-created_at')
    serializer_class = CookieExtractionJobSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.query_params.get('status')
        service_id = self.request.query_params.get('service_id')

        if status:
            queryset = queryset.filter(status=status)
        if service_id:
            queryset = queryset.filter(login_service__service_id=service_id)

        return queryset

class AdminCookieStatsView(APIView):
    """
    Admin endpoint to get comprehensive cookie management statistics.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        stats = {
            'total_login_services': LoginService.objects.count(),
            'active_login_services': LoginService.objects.filter(is_active=True).count(),
            'total_user_services': UserService.objects.count(),
            'active_user_services': UserService.objects.filter(status='active').count(),
            'pending_requests': UserService.objects.filter(status='pending').count(),
            'total_cookies': Cookie.objects.count(),
            'valid_cookies': Cookie.objects.filter(
                status='valid',
                expires_at__gt=timezone.now()
            ).count(),
            'expired_cookies': Cookie.objects.filter(
                Q(status='expired') | Q(expires_at__lte=timezone.now())
            ).count(),
            'recent_extractions': CookieExtractionJob.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'services_by_usage': self._get_services_by_usage(),
            'extraction_success_rate': self._get_extraction_success_rate()
        }

        serializer = CookieStatsSerializer(stats)
        return Response(serializer.data)

    def _get_services_by_usage(self):
        """Get services ordered by usage (cookie access count)"""
        services = UserService.objects.values(
            'service__name',
            'service__display_name'
        ).annotate(
            access_count=Count('access_count'),
            active_users=Count('id', filter=Q(status='active'))
        ).order_by('-access_count')[:10]

        return [
            {
                'service_name': service['service__name'],
                'display_name': service['service__display_name'],
                'total_access': service['access_count'],
                'active_users': service['active_users']
            }
            for service in services
        ]

    def _get_extraction_success_rate(self):
        """Calculate cookie extraction success rate"""
        total_jobs = CookieExtractionJob.objects.count()
        if total_jobs == 0:
            return 0.0

        successful_jobs = CookieExtractionJob.objects.filter(status='completed').count()
        return round((successful_jobs / total_jobs) * 100, 2)

class AdminCookieActivityView(generics.ListAPIView):
    """
    Admin endpoint to view all cookie injection activities.
    """
    queryset = CookieInjectionLog.objects.all().order_by('-timestamp')
    serializer_class = CookieInjectionLogSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        service_id = self.request.query_params.get('service_id')
        status = self.request.query_params.get('status')

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if service_id:
            queryset = queryset.filter(cookie__user_service__service_id=service_id)
        if status:
            queryset = queryset.filter(injection_status=status)

        return queryset

# ===== UTILITY ENDPOINTS =====

class ValidateCookiesView(APIView):
    """
    Admin endpoint to trigger validation of all pending cookies.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        pending_cookies = Cookie.objects.filter(status='pending_validation')
        validated_count = 0

        for cookie in pending_cookies:
            if cookie.validate_cookie():
                validated_count += 1

        return Response({
            "message": f"Validated {validated_count} out of {pending_cookies.count()} cookies",
            "validated_cookies": validated_count,
            "total_checked": pending_cookies.count()
        })

class CleanupExpiredDataView(APIView):
    """
    Admin endpoint to cleanup expired cookies and old logs.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        # Mark expired cookies
        expired_cookies = Cookie.objects.filter(
            expires_at__lte=timezone.now(),
            status='valid'
        )
        expired_count = expired_cookies.count()
        expired_cookies.update(status='expired')

        # Delete old injection logs (older than 30 days)
        cutoff_date = timezone.now() - timedelta(days=30)
        old_logs = CookieInjectionLog.objects.filter(timestamp__lt=cutoff_date)
        deleted_logs = old_logs.count()
        old_logs.delete()

        return Response({
            "message": "Cleanup completed",
            "expired_cookies": expired_count,
            "deleted_logs": deleted_logs
        })
