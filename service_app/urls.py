from django.urls import path
from .views import (
    # User endpoints
    AvailableServicesView,
    ServiceDetailView,
    UserAccessibleServicesView,
    UserServiceStatusView,
    RequestServiceAccessView,
    ServiceCookieAccessView,
    ServiceCategoriesView,
    # Admin endpoints
    AdminServiceListCreateView,
    AdminServiceDetailView,
    AdminUserServiceListView,
    AdminServiceStatsView,
)

urlpatterns = [
    # ==== USER ENDPOINTS ====

    # Browse all available services
    path('services/', AvailableServicesView.as_view(), name='available-services'),

    # Get specific service details
    path('services/<uuid:pk>/', ServiceDetailView.as_view(), name='service-detail'),

    # Get services user has access to through subscriptions
    path('user/accessible-services/', UserAccessibleServicesView.as_view(), name='user-accessible-services'),

    # Get user's service access status and cookie availability
    path('user/service-status/', UserServiceStatusView.as_view(), name='user-service-status'),

    # Request access to a specific service
    path('services/<uuid:service_id>/request-access/', RequestServiceAccessView.as_view(), name='request-service-access'),

    # Get cookie data for a specific service
    path('services/<uuid:service_id>/cookie/', ServiceCookieAccessView.as_view(), name='service-cookie-access'),

    # Get service categories
    path('categories/', ServiceCategoriesView.as_view(), name='service-categories'),

    # ==== ADMIN ENDPOINTS ====

    # Admin service management
    path('admin/services/', AdminServiceListCreateView.as_view(), name='admin-service-list-create'),
    path('admin/services/<uuid:pk>/', AdminServiceDetailView.as_view(), name='admin-service-detail'),

    # Admin user service assignments
    path('admin/user-services/', AdminUserServiceListView.as_view(), name='admin-user-service-list'),

    # Admin service statistics
    path('admin/stats/', AdminServiceStatsView.as_view(), name='admin-service-stats'),
    path('admin/stats/<uuid:service_id>/', AdminServiceStatsView.as_view(), name='admin-service-stats-detail'),
]
