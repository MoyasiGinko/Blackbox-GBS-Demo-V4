from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'is_verified', 'date_joined')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'full_name', 'password')

    def create(self, validated_data):
        try:
            user = User.objects.create_user(
                email=validated_data['email'],
                full_name=validated_data['full_name'],
                password=validated_data['password']
            )
            # Optionally send verification email here
            return user
        except Exception as e:
            raise serializers.ValidationError(f"Error creating user: {str(e)}")
