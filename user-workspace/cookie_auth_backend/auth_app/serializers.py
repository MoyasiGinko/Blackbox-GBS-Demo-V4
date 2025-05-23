from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'is_active', 'is_admin', 'date_joined']
        read_only_fields = ['id', 'is_admin', 'date_joined']
