from rest_framework import generics, permissions
from .models import Cookie
from .serializers import CookieSerializer

class CookieListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CookieSerializer

    def get_queryset(self):
        return Cookie.objects.filter(user_service__user=self.request.user)
