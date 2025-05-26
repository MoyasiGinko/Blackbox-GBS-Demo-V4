from rest_framework import generics, status, permissions
from rest_framework.response import Response
from .models import SubscriptionPlan, UserSubscription
from .serializers_v2 import SubscriptionPlanSerializer, UserSubscriptionSerializer
from django.utils import timezone
from datetime import timedelta

class SubscriptionPlanListView(generics.ListAPIView):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

class PurchaseSubscriptionView(generics.CreateAPIView):
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        duration = data.get('duration_days', 30)
        data['expires_at'] = timezone.now() + timedelta(days=duration)
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
