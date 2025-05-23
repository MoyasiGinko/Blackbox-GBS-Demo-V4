from django.urls import path
from .views import UserProfileView, AdminUserListView

urlpatterns = [
    path('user/profile/', UserProfileView.as_view(), name='user-profile'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
]
