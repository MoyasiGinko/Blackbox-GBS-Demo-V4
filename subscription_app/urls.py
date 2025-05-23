from django.urls import path
from .views import SubscriptionListView, PaymentListView

urlpatterns = [
    path('subscriptions/', SubscriptionListView.as_view(), name='subscription-list'),
    path('payments/', PaymentListView.as_view(), name='payment-list'),
]
