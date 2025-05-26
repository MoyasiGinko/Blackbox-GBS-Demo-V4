from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'max_services', 'is_active', 'created_at')
    search_fields = ('name',)
    list_filter = ('is_active',)

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription', 'is_active', 'purchased_at', 'expires_at')
    search_fields = ('user__email', 'subscription__name')
    list_filter = ('is_active',)
