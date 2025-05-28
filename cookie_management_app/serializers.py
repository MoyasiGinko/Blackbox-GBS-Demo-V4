from rest_framework import serializers
from django.utils import timezone
from .models import LoginService, UserService, Cookie, CookieInjectionLog, CookieExtractionJob
from service_app.serializers import ServiceSerializer
from auth_app.models import User

# ===== LOGIN SERVICE SERIALIZERS =====

class LoginServiceSerializer(serializers.ModelSerializer):
    """Basic login service serializer"""
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_display_name = serializers.CharField(source='service.display_name', read_only=True)
    available_slots = serializers.SerializerMethodField()

    class Meta:
        model = LoginService
        fields = [
            'id', 'service', 'service_name', 'service_display_name', 'username',
            'is_active', 'max_concurrent_users', 'current_users', 'available_slots',
            'created_at', 'updated_at', 'last_login_attempt'
        ]
        read_only_fields = ['id', 'current_users', 'created_at', 'updated_at']

    def get_available_slots(self, obj):
        return obj.get_available_slots()

class CreateLoginServiceSerializer(serializers.ModelSerializer):
    """Serializer for creating login services"""
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = LoginService
        fields = [
            'service', 'username', 'password', 'additional_credentials',
            'max_concurrent_users', 'is_active'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        # Here you would encrypt the password
        validated_data['encrypted_password'] = f"encrypted_{password}"  # Mock encryption
        return LoginService.objects.create(**validated_data)

class LoginServiceDetailSerializer(serializers.ModelSerializer):
    """Detailed login service serializer with related data"""
    service = ServiceSerializer(read_only=True)
    active_users = serializers.SerializerMethodField()
    recent_extractions = serializers.SerializerMethodField()

    class Meta:
        model = LoginService
        fields = [
            'id', 'service', 'username', 'additional_credentials',
            'is_active', 'max_concurrent_users', 'current_users',
            'active_users', 'recent_extractions', 'created_at', 'updated_at',
            'last_login_attempt'
        ]

    def get_active_users(self, obj):
        return obj.userservice_set.filter(status='active').count()

    def get_recent_extractions(self, obj):
        return obj.extraction_jobs.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()

# ===== USER SERVICE SERIALIZERS =====

class UserServiceSerializer(serializers.ModelSerializer):
    """Basic user service serializer"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    login_service_username = serializers.CharField(source='login_service.username', read_only=True)

    class Meta:
        model = UserService
        fields = [
            'id', 'user', 'user_email', 'service', 'service_name',
            'login_service', 'login_service_username', 'status',
            'assigned_at', 'last_accessed', 'access_count'
        ]
        read_only_fields = ['id', 'assigned_at', 'access_count']

class CreateUserServiceRequestSerializer(serializers.ModelSerializer):
    """Serializer for creating user service access requests"""
    class Meta:
        model = UserService
        fields = ['service']

    def create(self, validated_data):
        user = self.context['request'].user
        service = validated_data['service']

        # Check if user has active subscription for this service
        if not user.has_active_subscription():
            raise serializers.ValidationError("No active subscription found")

        # Check if user has access to this service through subscription
        accessible_services = user.get_accessible_services()
        if service not in accessible_services:
            raise serializers.ValidationError("Service not included in your subscription")

        # Create or get existing request
        user_service, created = UserService.objects.get_or_create(
            user=user,
            service=service,
            defaults={'status': 'pending'}
        )

        if not created and user_service.status == 'active':
            raise serializers.ValidationError("You already have active access to this service")

        return user_service

class UserServiceDetailSerializer(serializers.ModelSerializer):
    """Detailed user service serializer with related data"""
    user = serializers.StringRelatedField()
    service = ServiceSerializer(read_only=True)
    login_service = LoginServiceSerializer(read_only=True)
    active_cookies = serializers.SerializerMethodField()
    last_cookie_update = serializers.SerializerMethodField()

    class Meta:
        model = UserService
        fields = [
            'id', 'user', 'service', 'login_service', 'status',
            'assigned_at', 'last_accessed', 'access_count',
            'active_cookies', 'last_cookie_update'
        ]

    def get_active_cookies(self, obj):
        return obj.cookies.filter(status='valid', expires_at__gt=timezone.now()).count()

    def get_last_cookie_update(self, obj):
        latest_cookie = obj.cookies.order_by('-extracted_at').first()
        return latest_cookie.extracted_at if latest_cookie else None

# ===== COOKIE SERIALIZERS =====

class CookieSerializer(serializers.ModelSerializer):
    """Basic cookie serializer"""
    user_email = serializers.CharField(source='user_service.user.email', read_only=True)
    service_name = serializers.CharField(source='user_service.service.name', read_only=True)
    is_expired = serializers.SerializerMethodField()
    time_until_expiry = serializers.SerializerMethodField()

    class Meta:
        model = Cookie
        fields = [
            'id', 'user_email', 'service_name', 'session_id',
            'extracted_at', 'expires_at', 'last_validated', 'status',
            'validation_attempts', 'is_expired', 'time_until_expiry'
        ]

    def get_is_expired(self, obj):
        return obj.is_expired()

    def get_time_until_expiry(self, obj):
        if obj.is_expired():
            return None
        delta = obj.expires_at - timezone.now()
        return int(delta.total_seconds())

class CookieDataSerializer(serializers.ModelSerializer):
    """Serializer for returning cookie data to users"""
    service_info = serializers.SerializerMethodField()

    class Meta:
        model = Cookie
        fields = ['id', 'cookie_data', 'session_id', 'expires_at', 'service_info']

    def get_service_info(self, obj):
        return {
            'name': obj.user_service.service.name,
            'display_name': obj.user_service.service.display_name,
            'login_url': obj.user_service.service.login_url
        }

class CreateCookieSerializer(serializers.ModelSerializer):
    """Serializer for creating cookies (admin use)"""
    class Meta:
        model = Cookie
        fields = ['user_service', 'cookie_data', 'session_id', 'expires_at']

    def create(self, validated_data):
        validated_data['status'] = 'pending_validation'
        cookie = Cookie.objects.create(**validated_data)
        # Trigger validation
        cookie.validate_cookie()
        return cookie

# ===== COOKIE INJECTION LOG SERIALIZERS =====

class CookieInjectionLogSerializer(serializers.ModelSerializer):
    """Cookie injection log serializer"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    service_name = serializers.CharField(source='cookie.user_service.service.name', read_only=True)

    class Meta:
        model = CookieInjectionLog
        fields = [
            'id', 'user_email', 'service_name', 'injection_status',
            'message', 'timestamp', 'ip_address', 'user_agent'
        ]

# ===== COOKIE EXTRACTION JOB SERIALIZERS =====

class CookieExtractionJobSerializer(serializers.ModelSerializer):
    """Cookie extraction job serializer"""
    service_name = serializers.CharField(source='login_service.service.name', read_only=True)
    login_service_username = serializers.CharField(source='login_service.username', read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = CookieExtractionJob
        fields = [
            'id', 'service_name', 'login_service_username', 'status',
            'created_at', 'started_at', 'completed_at', 'error_message',
            'extracted_cookies_count', 'duration'
        ]

    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            delta = obj.completed_at - obj.started_at
            return int(delta.total_seconds())
        return None

class CreateExtractionJobSerializer(serializers.Serializer):
    """Serializer for triggering cookie extraction"""
    login_service_id = serializers.UUIDField()

    def validate_login_service_id(self, value):
        try:
            login_service = LoginService.objects.get(id=value, is_active=True)
            return value
        except LoginService.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive login service")

# ===== STATISTICS SERIALIZERS =====

class CookieStatsSerializer(serializers.Serializer):
    """Serializer for cookie management statistics"""
    total_login_services = serializers.IntegerField()
    active_login_services = serializers.IntegerField()
    total_user_services = serializers.IntegerField()
    active_user_services = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    total_cookies = serializers.IntegerField()
    valid_cookies = serializers.IntegerField()
    expired_cookies = serializers.IntegerField()
    recent_extractions = serializers.IntegerField()
    services_by_usage = serializers.ListField()
    extraction_success_rate = serializers.FloatField()
