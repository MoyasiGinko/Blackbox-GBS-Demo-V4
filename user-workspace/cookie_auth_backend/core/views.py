from rest_framework import generics, permissions
from .models import User, Subscription, Payment, Service
from .models_part2 import UserService, Cookie
from .serializers import UserSerializer, ServiceSerializer, SubscriptionSerializer, CookieSerializer, PaymentSerializer

class UserProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class AdminUserListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = UserSerializer
    queryset = User.objects.all()

class ServiceListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = ServiceSerializer
    queryset = Service.objects.all()

class SubscriptionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.all()

class UserServiceListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServiceSerializer

    def get_queryset(self):
        return UserService.objects.filter(user=self.request.user)

class CookieListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CookieSerializer

    def get_queryset(self):
        return Cookie.objects.filter(user_service__user=self.request.user)

class PaymentListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)
