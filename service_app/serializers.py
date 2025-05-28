from rest_framework import serializers
from .models import Service
from cookie_management_app.models import UserService

class ServiceSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Service
        fields = '__all__'

class UserServiceSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    service_name = serializers.CharField(source='service.display_name', read_only=True)
    last_cookie_update = serializers.SerializerMethodField()
    has_valid_cookies = serializers.SerializerMethodField()

    class Meta:
        model = UserService
        fields = '__all__'

    def get_last_cookie_update(self, obj):
        """Get the timestamp of the most recent valid cookie."""
        latest_cookie = obj.cookies.filter(status='valid').order_by('-extracted_at').first()
        return latest_cookie.extracted_at if latest_cookie else None

    def get_has_valid_cookies(self, obj):
        """Check if this user service has valid cookies available."""
        from django.utils import timezone
        return obj.cookies.filter(
            status='valid',
            expires_at__gt=timezone.now()
        ).exists()

class ServiceCategorySerializer(serializers.Serializer):
    category = serializers.CharField()
    display_name = serializers.CharField()
    service_count = serializers.IntegerField()

class ServiceStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    valid_cookies = serializers.IntegerField()
    login_services = serializers.IntegerField()
