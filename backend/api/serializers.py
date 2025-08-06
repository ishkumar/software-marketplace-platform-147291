from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework import serializers
from .models import User

# PUBLIC_INTERFACE
class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    class Meta:
        model = User
        fields = ('username', 'email', 'full_name', 'password')
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.provider = 'local'
        user.save()
        return user

# PUBLIC_INTERFACE
class LoginSerializer(serializers.Serializer):
    """Serializer for authenticating user credentials."""
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("User is disabled.")
        update_last_login(None, user)
        return {"user": user}

# PUBLIC_INTERFACE
class UserSerializer(serializers.ModelSerializer):
    """Serializer for displaying user details."""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'full_name', 'avatar_url', 'provider', 'is_publisher')
