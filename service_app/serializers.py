from rest_framework import serializers
from .models import Service
from cookie_management_app.models import UserService

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class UserServiceSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    
    class Meta:
        model = UserService
        fields = '__all__'
