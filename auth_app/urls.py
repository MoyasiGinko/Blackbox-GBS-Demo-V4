from django.urls import path
from .views import RegisterView, UserProfileView, AdminUserListView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
]
