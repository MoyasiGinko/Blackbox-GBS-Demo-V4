from django.urls import path
from .views import (
    # User endpoints
    CreatePaymentView,
    ProcessPaymentView,
    UserPaymentHistoryView,
    UserPaymentDetailView,
    UserPaymentStatsView,
    # Admin endpoints
    AdminPaymentListView,
    AdminPaymentDetailView,
    AdminRefundPaymentView,
    AdminPaymentStatsView,
)

urlpatterns = [
    # ==== USER ENDPOINTS ====
    # Payment creation and processing
    path('create/', CreatePaymentView.as_view(), name='payment-create'),
    path('process/', ProcessPaymentView.as_view(), name='payment-process'),

    # User payment management
    path('my-payments/', UserPaymentHistoryView.as_view(), name='user-payment-history'),
    path('my-payments/<uuid:pk>/', UserPaymentDetailView.as_view(), name='user-payment-detail'),
    path('my-stats/', UserPaymentStatsView.as_view(), name='user-payment-stats'),

    # ==== ADMIN ENDPOINTS ====
    # Admin payment management
    path('admin/payments/', AdminPaymentListView.as_view(), name='admin-payment-list'),
    path('admin/payments/<uuid:pk>/', AdminPaymentDetailView.as_view(), name='admin-payment-detail'),
    path('admin/refund/', AdminRefundPaymentView.as_view(), name='admin-payment-refund'),
    path('admin/stats/', AdminPaymentStatsView.as_view(), name='admin-payment-stats'),
]
