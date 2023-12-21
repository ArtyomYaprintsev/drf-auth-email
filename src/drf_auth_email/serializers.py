from rest_framework import serializers

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _


LINK_FIELD_HELP_TEXT = \
    'the link which can be send with the generated code inside email message'


class SignupSerializer(serializers.Serializer):
    """User signup serializer."""

    email = serializers.EmailField(max_length=255, help_text='the user email')
    password = serializers.CharField(
        max_length=128,
        help_text='the user password',
    )
    link = serializers.URLField(
        required=False,
        help_text=LINK_FIELD_HELP_TEXT,
    )

    first_name = serializers.CharField(
        max_length=150,
        required=False,
        help_text='the user first name',
    )
    last_name = serializers.CharField(
        max_length=150,
        required=False,
        help_text='the user last name',
    )


class PasswordResetSerializer(serializers.Serializer):
    """User password reset serializer."""

    email = serializers.EmailField(
        max_length=255,
        help_text='the user related email',
    )
    link = serializers.URLField(
        required=False,
        help_text=LINK_FIELD_HELP_TEXT,
    )


class PasswordResetVerifiedSerializer(serializers.Serializer):
    """Confirm password reset serializer."""

    password = serializers.CharField(max_length=128, help_text='new password')


class EmailChangeSerializer(serializers.Serializer):
    """Email change serializer."""

    email = serializers.EmailField(max_length=255, help_text='new email')
    link = serializers.URLField(
        required=False,
        help_text=LINK_FIELD_HELP_TEXT,
    )


class PasswordChangeSerializer(serializers.Serializer):
    """Password change serializer."""

    password = serializers.CharField(
        max_length=128,
        help_text='current password',
    )
    new_password = serializers.CharField(
        max_length=128,
        help_text='new password',
    )


class LoginSerializer(serializers.Serializer):
    """User login serializer."""

    email = serializers.EmailField(
        max_length=255,
        help_text='the user email',
    )
    password = serializers.CharField(
        max_length=128,
        help_text='the user password',
    )


class UserSerializer(serializers.ModelSerializer):
    """User model serializer.

    On `update()` or `create()` methods call generates hashed password from
    the provided password field.
    """

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


class DetailErrorSerializer(serializers.Serializer):
    """Detail error serializer.

    Used in OpenAPI schema only.
    """

    detail = serializers.CharField(help_text='error message')


class SuccessMessageSerializer(serializers.Serializer):
    """Success message serializer.

    Used in OpenAPI schema only.
    """
    success = serializers.CharField(help_text='success message')


class SuccessMessageWithEmailSerializer(serializers.Serializer):
    """Success message serializer.

    Contains additional `email` field. Used in OpenAPI schema only.
    """
    email = serializers.EmailField(help_text='success action related email')


class TokenSerializer(serializers.Serializer):
    """User authentication token serializer.

    Used in OpenAPI schema only.
    """
    token = serializers.CharField(help_text='user authentication token')
