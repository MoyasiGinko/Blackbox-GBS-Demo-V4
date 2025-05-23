from rest_framework import serializers
from .models import User, Subscription, Payment, Service
from .models_part2 import UserService, Cookie

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'is_active', 'is_admin', 'date_joined', 'subscription']
        read_only_fields = ['id', 'is_admin', 'date_joined']

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'

class UserServiceSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    class Meta:
        model = UserService
        fields = '__all__'

class CookieSerializer(serializers.ModelSerializer):
    user_service = UserServiceSerializer(read_only=True)
    class Meta:
        model = Cookie
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)
    class Meta:
        model = Payment
        fields = '__all__'
