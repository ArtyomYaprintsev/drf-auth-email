from rest_framework import serializers

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _


class SignupSerializer(serializers.Serializer):
    """Signup functionality serializer."""

    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=128)
    link = serializers.URLField(required=False)

    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    link = serializers.URLField(required=False)


class PasswordResetVerifiedSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=128)


class EmailChangeSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    link = serializers.URLField(required=False)


class PasswordChangeSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=128)
    new_password = serializers.CharField(max_length=128)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=128)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'password', 'first_name', 'last_name')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def update(self, instance, validated_data):
        validated_data['password'] = make_password(
            validated_data.get('password'),
        )
        return super().update(instance, validated_data)

    def create(self, validated_data):
        validated_data['password'] = make_password(
            validated_data.get('password'),
        )
        return super(UserSerializer, self).create(validated_data)
