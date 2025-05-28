from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q
from .models import Service
from cookie_management_app.models import UserService, Cookie, LoginService
from subscription_app.models import UserSubscription
from .serializers import ServiceSerializer, UserServiceSerializer, ServiceCategorySerializer
from cookie_management_app.serializers import CookieSerializer

# ==== USER ENDPOINTS ====

class AvailableServicesView(generics.ListAPIView):
    """
    List all available services for users to browse.
    Users can see all active services regardless of subscription.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServiceSerializer

    def get_queryset(self):
        return Service.objects.filter(is_active=True).order_by('category', 'display_name')

class ServiceDetailView(generics.RetrieveAPIView):
    """
    Get detailed information about a specific service.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServiceSerializer
    queryset = Service.objects.filter(is_active=True)

class UserAccessibleServicesView(generics.ListAPIView):
    """
    List services that the user has access to through active subscriptions.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServiceSerializer

    def get_queryset(self):
        user = self.request.user
        # Get user's active subscriptions
        active_subscriptions = UserSubscription.objects.filter(
            user=user,
            is_active=True,
            expires_at__gt=timezone.now()
        )

        # Get all service IDs from active subscriptions
        service_ids = set()
        for subscription in active_subscriptions:
            if subscription.selected_services.exists():
                # User selected specific services
                service_ids.update(subscription.selected_services.values_list('id', flat=True))
            else:
                # User gets access to all services in the plan
                service_ids.update(subscription.subscription.services.values_list('id', flat=True))

        return Service.objects.filter(id__in=service_ids, is_active=True)

class UserServiceStatusView(generics.ListAPIView):
    """
    List user's service access status and cookie availability.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserServiceSerializer

    def get_queryset(self):
        return UserService.objects.filter(user=self.request.user).select_related('service', 'login_service')

class RequestServiceAccessView(APIView):
    """
    Request access to a specific service.
    Only works if user has an active subscription that includes this service.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, service_id):
        try:
            service = Service.objects.get(id=service_id, is_active=True)
        except Service.DoesNotExist:
            return Response({"error": "Service not found."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        # Check if user has access through subscription
        accessible_services = self._get_user_accessible_services(user)
        if service not in accessible_services:
            return Response(
                {"error": "You don't have an active subscription for this service."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if user already has access
        user_service, created = UserService.objects.get_or_create(
            user=user,
            service=service,
            defaults={'is_active': True}
        )

        if not created:
            return Response(
                {"detail": "Access already granted for this service.", "user_service_id": str(user_service.id)},
                status=status.HTTP_200_OK
            )

        serializer = UserServiceSerializer(user_service)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _get_user_accessible_services(self, user):
        """Helper method to get user's accessible services."""
        active_subscriptions = UserSubscription.objects.filter(
            user=user,
            is_active=True,
            expires_at__gt=timezone.now()
        )

        service_ids = set()
        for subscription in active_subscriptions:
            if subscription.selected_services.exists():
                service_ids.update(subscription.selected_services.values_list('id', flat=True))
            else:
                service_ids.update(subscription.subscription.services.values_list('id', flat=True))

        return Service.objects.filter(id__in=service_ids, is_active=True)

class ServiceCookieAccessView(APIView):
    """
    Get cookie data for a specific service that user has access to.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, service_id):
        try:
            service = Service.objects.get(id=service_id, is_active=True)
        except Service.DoesNotExist:
            return Response({"error": "Service not found."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        # Check if user has access to this service
        try:
            user_service = UserService.objects.get(user=user, service=service, is_active=True)
        except UserService.DoesNotExist:
            return Response(
                {"error": "You don't have access to this service. Please request access first."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get valid cookie
        valid_cookie = Cookie.objects.filter(
            user_service=user_service,
            status='valid',
            expires_at__gt=timezone.now()
        ).first()

        if not valid_cookie:
            return Response(
                {"error": "No valid cookies available. Please try again later.", "status": "no_cookies"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Update last accessed time
        user_service.last_accessed = timezone.now()
        user_service.save()

        serializer = CookieSerializer(valid_cookie)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ServiceCategoriesView(APIView):
    """
    Get all service categories with service counts.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        categories = Service.objects.filter(is_active=True).values('category').distinct()
        category_data = []

        for cat in categories:
            category = cat['category']
            count = Service.objects.filter(category=category, is_active=True).count()
            category_data.append({
                'category': category,
                'display_name': dict(Service._meta.get_field('category').choices).get(category, category),
                'service_count': count
            })

        return Response(category_data, status=status.HTTP_200_OK)

# ==== ADMIN ENDPOINTS ====

class AdminServiceListCreateView(generics.ListCreateAPIView):
    """
    Admin endpoint to list and create services.
    """
    permission_classes = [permissions.IsAdminUser]
    serializer_class = ServiceSerializer
    queryset = Service.objects.all()

    def get_queryset(self):
        queryset = Service.objects.all().order_by('category', 'display_name')
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset

class AdminServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin endpoint to retrieve, update, or delete a service.
    """
    permission_classes = [permissions.IsAdminUser]
    serializer_class = ServiceSerializer
    queryset = Service.objects.all()

class AdminUserServiceListView(generics.ListAPIView):
    """
    Admin endpoint to view all user service assignments.
    """
    permission_classes = [permissions.IsAdminUser]
    serializer_class = UserServiceSerializer

    def get_queryset(self):
        queryset = UserService.objects.all().select_related('user', 'service', 'login_service')

        # Filter by service
        service_id = self.request.query_params.get('service_id')
        if service_id:
            queryset = queryset.filter(service_id=service_id)

        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter by status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.order_by('-assigned_at')

class AdminServiceStatsView(APIView):
    """
    Admin endpoint to get service usage statistics.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, service_id=None):
        if service_id:
            # Stats for a specific service
            try:
                service = Service.objects.get(id=service_id)
            except Service.DoesNotExist:
                return Response({"error": "Service not found."}, status=status.HTTP_404_NOT_FOUND)

            stats = {
                'service': ServiceSerializer(service).data,
                'total_users': UserService.objects.filter(service=service).count(),
                'active_users': UserService.objects.filter(service=service, is_active=True).count(),
                'valid_cookies': Cookie.objects.filter(
                    user_service__service=service,
                    status='valid',
                    expires_at__gt=timezone.now()
                ).count(),
                'login_services': LoginService.objects.filter(service=service, is_active=True).count()
            }
        else:
            # Overall stats
            stats = {
                'total_services': Service.objects.filter(is_active=True).count(),
                'total_user_services': UserService.objects.count(),
                'active_user_services': UserService.objects.filter(is_active=True).count(),
                'total_valid_cookies': Cookie.objects.filter(
                    status='valid',
                    expires_at__gt=timezone.now()
                ).count(),
                'services_by_category': self._get_services_by_category()
            }

        return Response(stats, status=status.HTTP_200_OK)

    def _get_services_by_category(self):
        """Helper method to get service counts by category."""
        categories = Service.objects.filter(is_active=True).values('category').distinct()
        category_stats = []

        for cat in categories:
            category = cat['category']
            count = Service.objects.filter(category=category, is_active=True).count()
            category_stats.append({
                'category': category,
                'count': count
            })

        return category_stats
