from rest_framework import generics, status, permissions
from rest_framework.response import Response
from .models import LoginService, Cookie, UserService
from .serializers import LoginServiceSerializer, CookieSerializer, UserServiceSerializer
from django.utils import timezone

class AddLoginServiceView(generics.CreateAPIView):
    serializer_class = LoginServiceSerializer
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetCookieDataView(generics.RetrieveAPIView):
    serializer_class = CookieSerializer
    queryset = Cookie.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            cookie = self.get_object()
            if cookie.status != 'valid' or cookie.expires_at < timezone.now():
                return Response({"detail": "Cookie expired or invalid."}, status=status.HTTP_400_BAD_REQUEST)
            # Check if user has access to this cookie's service
            user = request.user
            if not UserService.objects.filter(user=user, service=cookie.login_service.service, status='active').exists():
                return Response({"detail": "Access denied for this cookie."}, status=status.HTTP_403_FORBIDDEN)
            return Response(self.get_serializer(cookie).data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ListPendingUserServiceRequestsView(generics.ListAPIView):
    """
    Admin view to list all pending user service access requests.
    """
    serializer_class = UserServiceSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        # Filter UserService objects where is_active is False (pending)
        return UserService.objects.filter(is_active=False)

class ApproveUserServiceRequestView(generics.UpdateAPIView):
    """
    Admin view to approve a user service access request.
    """
    serializer_class = UserServiceSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = UserService.objects.filter(is_active=False)

    def patch(self, request, *args, **kwargs):
        user_service = self.get_object()
        user_service.is_active = True
        user_service.save()
        serializer = self.get_serializer(user_service)
        return Response(serializer.data)
