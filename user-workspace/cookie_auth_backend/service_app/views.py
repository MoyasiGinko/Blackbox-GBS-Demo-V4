from rest_framework import generics, permissions
from .models import Service, UserService
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
