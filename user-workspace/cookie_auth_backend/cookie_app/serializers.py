from rest_framework import serializers
from .models import Cookie, CookieInjectionLog
from service_app.serializers import UserServiceSerializer

class CookieSerializer(serializers.ModelSerializer):
    user_service = UserServiceSerializer(read_only=True)
    
    class Meta:
        model = Cookie
        fields = '__all__'

class CookieInjectionLogSerializer(serializers.ModelSerializer):
    cookie = CookieSerializer(read_only=True)
    
    class Meta:
        model = CookieInjectionLog
        fields = '__all__'
