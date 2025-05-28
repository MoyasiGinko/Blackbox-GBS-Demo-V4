from django.urls import path
from .views import (
    # User endpoints
    RequestServiceAccessView,
    UserAccessibleServicesView,
    GetServiceCookieView,
    UserServiceHistoryView,
    UserCookieActivityView,

    # Admin endpoints - Login Services
    AdminLoginServiceListView,
    AdminLoginServiceDetailView,

    # Admin endpoints - User Service Management
    AdminPendingRequestsView,
    AdminApproveServiceRequestView,
    AdminRejectServiceRequestView,
    AdminUserServicesView,

    # Admin endpoints - Cookie Management
    AdminCookieListView,
    AdminCookieDetailView,
    AdminTriggerCookieExtractionView,
    AdminExtractionJobsView,
    AdminCookieActivityView,

    # Admin endpoints - Statistics and Monitoring
    AdminCookieStatsView,

    # Utility endpoints
    ValidateCookiesView,
    CleanupExpiredDataView,
)

urlpatterns = [
    # ===== USER ENDPOINTS =====

    # Service access management
    path('request-access/', RequestServiceAccessView.as_view(), name='request-service-access'),
    path('my-services/', UserAccessibleServicesView.as_view(), name='user-accessible-services'),
    path('service/<uuid:service_id>/cookie/', GetServiceCookieView.as_view(), name='get-service-cookie'),
    path('my-history/', UserServiceHistoryView.as_view(), name='user-service-history'),
    path('my-activity/', UserCookieActivityView.as_view(), name='user-cookie-activity'),

    # ===== ADMIN ENDPOINTS =====

    # Login service management
    path('admin/login-services/', AdminLoginServiceListView.as_view(), name='admin-login-services'),
    path('admin/login-services/<uuid:pk>/', AdminLoginServiceDetailView.as_view(), name='admin-login-service-detail'),

    # User service request management
    path('admin/pending-requests/', AdminPendingRequestsView.as_view(), name='admin-pending-requests'),
    path('admin/approve-request/<uuid:user_service_id>/', AdminApproveServiceRequestView.as_view(), name='admin-approve-request'),
    path('admin/reject-request/<uuid:user_service_id>/', AdminRejectServiceRequestView.as_view(), name='admin-reject-request'),
    path('admin/user-services/', AdminUserServicesView.as_view(), name='admin-user-services'),

    # Cookie management
    path('admin/cookies/', AdminCookieListView.as_view(), name='admin-cookies'),
    path('admin/cookies/<uuid:pk>/', AdminCookieDetailView.as_view(), name='admin-cookie-detail'),
    path('admin/extract-cookies/', AdminTriggerCookieExtractionView.as_view(), name='admin-trigger-extraction'),
    path('admin/extraction-jobs/', AdminExtractionJobsView.as_view(), name='admin-extraction-jobs'),
    path('admin/cookie-activity/', AdminCookieActivityView.as_view(), name='admin-cookie-activity'),

    # Statistics and monitoring
    path('admin/stats/', AdminCookieStatsView.as_view(), name='admin-cookie-stats'),

    # ===== UTILITY ENDPOINTS =====

    # Maintenance operations
    path('admin/validate-cookies/', ValidateCookiesView.as_view(), name='validate-cookies'),
    path('admin/cleanup/', CleanupExpiredDataView.as_view(), name='cleanup-expired-data'),
]
