from django.urls import path
from .views import SubscriptionPlanListView, PurchaseSubscriptionView

urlpatterns = [
    path('plans/', SubscriptionPlanListView.as_view(), name='subscription-plan-list'),
    path('purchase/', PurchaseSubscriptionView.as_view(), name='purchase-subscription'),
]
