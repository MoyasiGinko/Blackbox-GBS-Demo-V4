from rest_framework import serializers
from .models import LoginService, UserService, Cookie, CookieInjectionLog

class LoginServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginService
        fields = '__all__'

class UserServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserService
        fields = '__all__'

class CookieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cookie
        fields = '__all__'

class CookieInjectionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CookieInjectionLog
        fields = '__all__'
