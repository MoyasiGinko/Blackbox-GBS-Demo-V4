from django.urls import path
from .views import CreatePaymentView

urlpatterns = [
    path('payments/create/', CreatePaymentView.as_view(), name='payment-create'),
]
