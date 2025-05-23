from django.urls import path
from .views import (
    UserProfileView,
    AdminUserListView,
    ServiceListCreateView,
    SubscriptionListView,
    UserServiceListView,
    CookieListView,
    PaymentListView,
)

urlpatterns = [
    path('user/profile/', UserProfileView.as_view(), name='user-profile'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('services/', ServiceListCreateView.as_view(), name='service-list-create'),
    path('subscriptions/', SubscriptionListView.as_view(), name='subscription-list'),
    path('user-services/', UserServiceListView.as_view(), name='user-service-list'),
    path('cookies/', CookieListView.as_view(), name='cookie-list'),
    path('payments/', PaymentListView.as_view(), name='payment-list'),
]
