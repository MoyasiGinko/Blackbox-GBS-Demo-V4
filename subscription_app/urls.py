from django.urls import path
from .views import (
    # User endpoints
    SubscriptionPlanListView,
    SubscriptionPlanDetailView,
    UserSubscriptionListView,
    UserActiveSubscriptionsView,
    PurchaseSubscriptionView,
    UpdateSubscriptionServicesView,
    CancelSubscriptionView,
    SubscriptionStatsView,
    # Admin endpoints
    AdminSubscriptionPlanListCreateView,
    AdminSubscriptionPlanDetailView,
    AdminUserSubscriptionListView,
    AdminSubscriptionStatsView,
)

urlpatterns = [
    # ==== USER ENDPOINTS ====

    # Browse subscription plans
    path('plans/', SubscriptionPlanListView.as_view(), name='subscription-plan-list'),
    path('plans/<uuid:pk>/', SubscriptionPlanDetailView.as_view(), name='subscription-plan-detail'),

    # User subscription management
    path('my-subscriptions/', UserSubscriptionListView.as_view(), name='user-subscription-list'),
    path('my-subscriptions/active/', UserActiveSubscriptionsView.as_view(), name='user-active-subscriptions'),

    # Purchase and manage subscriptions
    path('purchase/', PurchaseSubscriptionView.as_view(), name='purchase-subscription'),
    path('subscriptions/<uuid:subscription_id>/services/', UpdateSubscriptionServicesView.as_view(), name='update-subscription-services'),
    path('subscriptions/<uuid:subscription_id>/cancel/', CancelSubscriptionView.as_view(), name='cancel-subscription'),

    # User statistics
    path('my-stats/', SubscriptionStatsView.as_view(), name='subscription-stats'),

    # ==== ADMIN ENDPOINTS ====

    # Admin subscription plan management
    path('admin/plans/', AdminSubscriptionPlanListCreateView.as_view(), name='admin-subscription-plan-list-create'),
    path('admin/plans/<uuid:pk>/', AdminSubscriptionPlanDetailView.as_view(), name='admin-subscription-plan-detail'),

    # Admin subscription management
    path('admin/subscriptions/', AdminUserSubscriptionListView.as_view(), name='admin-user-subscription-list'),

    # Admin statistics
    path('admin/stats/', AdminSubscriptionStatsView.as_view(), name='admin-subscription-stats'),
]
