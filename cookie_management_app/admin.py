from django.contrib import admin
from .models import LoginService, UserService, Cookie, CookieInjectionLog, CookieExtractionJob

@admin.register(LoginService)
class LoginServiceAdmin(admin.ModelAdmin):
    list_display = ('service', 'username', 'is_active', 'max_concurrent_users', 'current_users', 'created_at', 'updated_at')
    search_fields = ('service__name', 'username')
    list_filter = ('is_active', 'service')
    readonly_fields = ('current_users', 'created_at', 'updated_at')

@admin.register(UserService)
class UserServiceAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'login_service', 'status', 'assigned_at', 'last_accessed', 'access_count')
    search_fields = ('user__email', 'service__name')
    list_filter = ('status', 'service')
    readonly_fields = ('assigned_at', 'access_count')

@admin.register(Cookie)
class CookieAdmin(admin.ModelAdmin):
    list_display = ('user_service', 'session_id', 'extracted_at', 'expires_at', 'last_validated', 'status', 'validation_attempts')
    search_fields = ('user_service__user__email', 'session_id')
    list_filter = ('status', 'user_service__service')
    readonly_fields = ('extracted_at', 'validation_attempts')

@admin.register(CookieInjectionLog)
class CookieInjectionLogAdmin(admin.ModelAdmin):
    list_display = ('cookie', 'user', 'injection_status', 'timestamp', 'ip_address')
    search_fields = ('user__email', 'cookie__id')
    list_filter = ('injection_status', 'timestamp')
    readonly_fields = ('timestamp',)

@admin.register(CookieExtractionJob)
class CookieExtractionJobAdmin(admin.ModelAdmin):
    list_display = ('login_service', 'status', 'created_at', 'started_at', 'completed_at', 'extracted_cookies_count')
    search_fields = ('login_service__service__name', 'login_service__username')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'extracted_cookies_count')
