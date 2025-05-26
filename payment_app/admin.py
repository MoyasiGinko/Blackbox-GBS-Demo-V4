from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'subscription_plan', 'amount', 'payment_status', 'payment_method', 'transaction_id', 'payment_date')
    search_fields = ('user__email', 'transaction_id')
    list_filter = ('payment_status', 'payment_method')
