from django.urls import path
from .views import SubscriptionPlanListView, PurchaseSubscriptionView

urlpatterns = [
    path('subscriptions/', SubscriptionPlanListView.as_view(), name='subscription-list'),
    path('subscriptions/purchase/', PurchaseSubscriptionView.as_view(), name='subscription-purchase'),
]
