"""Serializers for registration, the current user, and JWT login."""
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "display_name", "avatar_url")
        read_only_fields = ("id", "email")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ("id", "email", "username", "password", "display_name")

    def create(self, validated_data):
        # Use the manager so the password is hashed, never stored in plaintext.
        return User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],
            display_name=validated_data.get("display_name", ""),
        )


class EmailTokenObtainSerializer(TokenObtainPairSerializer):
    """Login serializer. Because USERNAME_FIELD='email', the field is `email`.
    We also embed a little user info in the response for the frontend."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
