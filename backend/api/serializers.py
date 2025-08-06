from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework import serializers
from .models import User, Listing, Like, Engagement

# PUBLIC_INTERFACE
class StripeCheckoutSessionSerializer(serializers.Serializer):
    """Serializer for starting a Stripe checkout session."""
    listing_id = serializers.IntegerField()
    transaction_type = serializers.ChoiceField(choices=["purchase", "subscription"])

# PUBLIC_INTERFACE
class StripeCheckoutSessionResponseSerializer(serializers.Serializer):
    """Return value for checkout session initiation."""
    session_url = serializers.CharField()

# PUBLIC_INTERFACE
class StripeWebhookSerializer(serializers.Serializer):
    """Minimal serializer for Stripe event webhook."""
    event_type = serializers.CharField()
    data = serializers.JSONField()

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


# PUBLIC_INTERFACE
class ListingSerializer(serializers.ModelSerializer):
    """Serializer for software listings."""
    publisher = UserSerializer(read_only=True)
    like_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'publisher', 'title', 'summary', 'application_type',
            'is_paid', 'price', 'download_url', 'external_link', 'created_at',
            'updated_at', 'tags', 'like_count'
        ]

    def get_like_count(self, obj):
        return obj.likes.count()


# PUBLIC_INTERFACE
class LikeSerializer(serializers.ModelSerializer):
    """Serializer for like on a listing."""
    user = UserSerializer(read_only=True)
    class Meta:
        model = Like
        fields = ['id', 'user', 'listing', 'created_at']


# PUBLIC_INTERFACE
class EngagementSerializer(serializers.ModelSerializer):
    """Serializer for engagement between user and publisher (messaging/contact)."""
    sender = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)

    class Meta:
        model = Engagement
        fields = [
            'id', 'sender', 'recipient', 'listing', 'message',
            'status', 'created_at'
        ]
