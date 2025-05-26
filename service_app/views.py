from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Service
from cookie_management_app.models import UserService
from .serializers import ServiceSerializer, UserServiceSerializer

class ServiceListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = ServiceSerializer
    queryset = Service.objects.all()

class UserServiceListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserServiceSerializer

    def get_queryset(self):
        return UserService.objects.filter(user=self.request.user)

class AvailableServicesView(generics.ListAPIView):
    """
    List all available services for users to browse.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServiceSerializer
    queryset = Service.objects.filter(is_active=True)

class RequestServiceAccessView(generics.CreateAPIView):
    """
    After payment, users can request access to a service.
    This creates a service access request for admin approval.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserServiceSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        service_id = request.data.get('service_id')
        if not service_id:
            return Response({"error": "Service ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        # Check if user already has access
        if UserService.objects.filter(user=user, service_id=service_id).exists():
            return Response({"detail": "Access already granted for this service."}, status=status.HTTP_400_BAD_REQUEST)
        # Create a new UserService request with status 'pending'
        user_service = UserService.objects.create(user=user, service_id=service_id, status='pending')
        serializer = self.get_serializer(user_service)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
