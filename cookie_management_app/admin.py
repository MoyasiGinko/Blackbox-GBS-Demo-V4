from django.contrib import admin
from .models import LoginService, UserService, Cookie, CookieInjectionLog

@admin.register(LoginService)
class LoginServiceAdmin(admin.ModelAdmin):
    list_display = ('service', 'username', 'is_active', 'max_concurrent_users', 'current_users', 'created_at', 'updated_at')
    search_fields = ('service__name', 'username')
    list_filter = ('is_active',)

@admin.register(UserService)
class UserServiceAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'login_service', 'is_active', 'assigned_at', 'last_accessed')
    search_fields = ('user__email', 'service__name')
    list_filter = ('is_active',)

@admin.register(Cookie)
class CookieAdmin(admin.ModelAdmin):
    list_display = ('user_service', 'session_id', 'extracted_at', 'expires_at', 'last_validated', 'status')
    search_fields = ('user_service__user__email', 'session_id')
    list_filter = ('status',)

@admin.register(CookieInjectionLog)
class CookieInjectionLogAdmin(admin.ModelAdmin):
    list_display = ('cookie', 'user', 'injection_status', 'timestamp', 'ip_address')
    search_fields = ('user__email', 'cookie__id')
    list_filter = ('injection_status',)
