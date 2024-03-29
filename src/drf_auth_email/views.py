from typing import Type
from ipware import get_client_ip
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from . import serializers, models, schemas
from .abstracts import AbstractCodeVerify
from .settings import settings
from .typing import Kwargs
from .compat import \
    extend_schema_view, extend_schema, OpenApiResponse, OpenApiExample


USER = get_user_model()
Code = Type[AbstractCodeVerify]


class ActionCodeVerifyView(GenericAPIView):
    permission_classes = (AllowAny,)
    action_code_model = None
    proceed_action = _('make action')

    def get_action_code_model(self):
        # TODO: add assert
        return self.action_code_model

    @extend_schema(
        parameters=[schemas.CodeQueryParameter],
        responses={
            200: OpenApiResponse(
                response=serializers.SuccessMessageSerializer,
                description='Action code is valid',
                examples=[
                    OpenApiExample(
                        'Code parameter is valid',
                        description='code parameter is valid',
                        value={
                            'success': 'The given `code` parameter is valid.',
                        },
                    ),
                ],
            ),
            400: schemas.ErrorCodeResponse,
        },
    )
    def get(self, request, format=None):
        """Verify the provided action code.

        The code may be invalid for some reasons, so make sure the code is
        valid before proceeding the requested action.
        """
        try:
            self.get_action_code_model().check_is_valid(request.GET.get('code'))
        except ValueError as err:
            return Response({
                'detail': str(err),
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': _(
                'The given `code` parameter is valid, can proceed to %s.'
            ) % self.proceed_action,
        })


class ActionVerifyView(GenericAPIView):
    permission_classes = (AllowAny,)
    action_code_model: Code = None
    success_message: str = None

    def get_action_code_model(self):
        # TODO: add assert
        return self.action_code_model

    def get_success_message(self):
        # TODO: ad assert
        return self.success_message

    def handle_action_code(self, action_code: Code, **kwargs) -> None:
        # Must be overridden
        pass

    def handle_request(self, request, action_code: Code) -> Kwargs | Response:
        # May be overridden
        return {}

    @extend_schema(
        parameters=[schemas.CodeQueryParameter],
        responses={
            400: schemas.ErrorCodeResponse,
        },
    )
    def post(self, request, format=None):
        try:
            action_code = self.get_action_code_model().check_is_valid(
                request.GET.get('code'),
                select_related_user=True,
            )
        except ValueError as err:
            return Response({
                'detail': str(err),
            }, status=status.HTTP_400_BAD_REQUEST)

        kwargs = self.handle_request(request, action_code)

        if isinstance(kwargs, Response):
            return kwargs

        self.handle_action_code(action_code, **kwargs)

        return Response({'success': self.success_message})


class Signup(GenericAPIView):
    permission_classes = (AllowAny,)
    signup_serializer_class = serializers.SignupSerializer
    user_serializer_class = serializers.UserSerializer
    signup_model = models.SignupCode

    def get_serializer_class(self):
        return self.signup_serializer_class

    def check_verified_users(self, serializer) -> USER:
        # Check verified user with the given email existence
        user, is_created = USER.objects.get_or_create(
            email=serializer.data.get('email'),
        )

        if not is_created and user.is_verified:
            raise ValueError(_('Email address already taken.'))

        return user

    @extend_schema(
        summary='create signup request',
        request=signup_serializer_class,
        responses={
            201: OpenApiResponse(
                response=user_serializer_class,
                description='New unverified user',
            ),
            400: OpenApiResponse(
                response=serializers.DetailErrorSerializer,
                description='The request body is invalid',
            )
        },
    )
    def post(self, request, format=None):
        """Create signup request with provided credentials.

        Accepts the user credentials, generates a signup verification code,
        and sends an email with a verification link.
        """
        signup_serializer = self.signup_serializer_class(
            data=request.data,
        )

        # Check serializer validation
        if not signup_serializer.is_valid():
            return Response(
                signup_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = self.check_verified_users(signup_serializer)
        except ValueError as err:
            return Response({
                'detail': str(err),
            }, status=status.HTTP_400_BAD_REQUEST)

        # handle unverified user with the given data
        user_serializer = self.user_serializer_class(
            user, data=signup_serializer.data, partial=True,
        )

        if not user_serializer.is_valid():
            return Response(
                user_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = user_serializer.save()

        # Handle signup code
        signup_code = self.signup_model.objects.create(
            user=user,
            ipaddr=get_client_ip(request)[0] or '0.0.0.0',
            link=signup_serializer.data.get('link') or '',
        )
        signup_code.send_email()

        # Return update user instance serializer
        return Response(user_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(get=extend_schema(summary='verify signup code'))
class SignupCodeVerify(ActionCodeVerifyView):
    action_code_model = models.SignupCode
    proceed_action = _('verify signup')


class SignupVerify(ActionVerifyView):
    action_code_model = models.SignupCode
    success_message = _('User email address has been verified.')

    def send_welcome_email(self, **kwargs):
        action_code = kwargs.get('action_code')

        # Send welcome email
        settings.USER_EMAILS_WELCOME.send_email(
            target=action_code.user.email,
            context={},
        )

    def handle_action_code(self, action_code: Code, **kwargs) -> None:
        # Verify user
        action_code.verify_user()

        self.send_welcome_email(action_code=action_code)

        # Delete all related to verified user signup codes
        self.action_code_model.objects.filter(user=action_code.user).delete()

    @extend_schema(
        summary='complete user signup',
        request=None,
        parameters=[schemas.CodeQueryParameter],
        responses={
            200: OpenApiResponse(
                response=serializers.SuccessMessageSerializer,
                description='',
                examples=[
                    OpenApiExample(
                        'Signup completed successfully',
                        value={'success': success_message},
                    ),
                ],
            ),
            400: schemas.ErrorCodeResponse,
        },
    )
    def post(self, request, format=None):
        """Confirm signup action.

        Sets the user related with the provided valid signup code as verified.

        Note:
            After verification, all signup codes related with the user are
            deleted.
        """
        return super().post(request, format)


class PasswordReset(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = serializers.PasswordResetSerializer
    password_reset_model = models.PasswordResetCode

    @extend_schema(
        summary='create password reset request',
        request=serializer_class,
        responses={
            201: OpenApiResponse(
                response=serializers.SuccessMessageWithEmailSerializer,
                description='The password reset request has been created',
                examples=[
                    OpenApiExample(
                        'Success password reset request creation',
                        value={
                            'success': 'Success message',
                            'email': 'example@email.com',
                        },
                        description=(
                            'A password reset message has been sent to '
                            '`example@email.com`. The user can continue '
                            'the action by clicking the sent link.'
                        ),
                    ),
                ],
            ),
            400: schemas.DetailErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """Create password reset request.

        Generates a new password reset code and sends it to the provided email.
        """
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Save way to get user with the provided email
        user = USER.objects.filter(email=serializer.data.get('email')).first()

        if user and user.is_verified and user.is_active:
            password_reset_code = self.password_reset_model.objects.create(
                user=user,
                ipaddr=get_client_ip(request)[0] or '0.0.0.0',
                link=serializer.data.get('link') or '',
            )

            password_reset_code.send_email()

            return Response({
                'success': _(
                    'The email with the password reset code will be sent soon.',
                ),
                'email': user.email,
            }, status=status.HTTP_201_CREATED)

        # Since this is AllowAny, don't give away error.
        return Response({
            'detail': _('Password reset not allowed.'),
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(get=extend_schema(summary='verify password reset code'))
class PasswordResetCodeVerify(ActionCodeVerifyView):
    action_code_model = models.PasswordResetCode
    proceed_action = _('password reset')


class PasswordResetVerify(ActionVerifyView):
    serializer_class = serializers.PasswordResetVerifiedSerializer
    action_code_model = models.PasswordResetCode
    success_message = _('User password has been reset.')

    def handle_request(self, request, action_code: Code) -> Kwargs | Response:
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        return {
            'serializer': serializer,
        }

    def handle_action_code(self, action_code: Code, **kwargs) -> None:
        serializer = kwargs.get('serializer')

        # Set new user password
        action_code.change_user_password(serializer.data.get('password'))

        # Delete all related password reset instances
        self.action_code_model.objects.filter(
            user=action_code.user,
        ).delete()

    @extend_schema(
        summary='complete password reset',
        request=serializer_class,
        parameters=[schemas.CodeQueryParameter],
        responses={
            200: OpenApiResponse(
                response=serializers.SuccessMessageSerializer,
                examples=[
                    OpenApiExample(
                        'Password reset completed successfully',
                        value={'success': success_message},
                    ),
                ],
            ),
            400: schemas.ErrorCodeResponse,
        },
    )
    def post(self, request, format=None):
        """Confirm password reset action.

        Updates the password field of the user related with the provided
        valid password reset code.

        Note:
            After update, all password reset codes related with the user are
            deleted.
        """
        return super().post(request, format)


class EmailChange(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.EmailChangeSerializer
    email_change_model = models.EmailChangeCode

    @extend_schema(
        summary='create email change request',
        request=serializer_class,
        responses={
            201: OpenApiResponse(
                response=serializers.SuccessMessageWithEmailSerializer,
                description='The email change request has been created',
                examples=[
                    OpenApiExample(
                        'Success email change request creation',
                        value={
                            'success': 'Success message',
                            'email': 'example@email.com',
                        },
                        description=(
                            'A email change message has been sent to '
                            '`example@email.com`. The user can continue '
                            'the action by clicking the sent link.'
                        ),
                    ),
                ],
            ),
            400: schemas.DetailErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """Create email change request.

        Generates a new email change code and sends it to the provided email.
        """
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_email = serializer.data.get('email')
        user_with_new_email = USER.objects.filter(email=new_email).first()

        if user_with_new_email and user_with_new_email.is_verified:
            return Response({
                'detail': _('Email address already taken.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        email_change_code = self.email_change_model.objects.create(
            user=request.user,
            new_email=new_email,
            ipaddr=get_client_ip(request)[0] or '0.0.0.0',
            link=serializer.data.get('link') or '',
        )
        email_change_code.send_email()

        return Response({
            'success': _(
                'The email with the email change code will be sent soon.',
            ),
            'email': new_email,
        }, status=status.HTTP_201_CREATED)


@extend_schema_view(get=extend_schema(summary='verify email change code'))
class EmailChangeCodeVerify(ActionCodeVerifyView):
    action_code_model = models.EmailChangeCode
    proceed_action = _('email change')


class EmailChangeVerify(ActionVerifyView):
    action_code_model = models.EmailChangeCode
    success_message = _('Email address has been changed.')

    def handle_request(self, request, action_code: Code) -> Kwargs | Response:
        user_with_new_email = (
            USER.objects.filter(email=action_code.new_email).first()
        )

        if user_with_new_email:
            if user_with_new_email.is_verified:
                return Response({
                    'detail': _('Email address already taken.'),
                }, status=status.HTTP_400_BAD_REQUEST)

            # If the account with this email address is not verified,
            # delete the account (and signup code) because the email
            # address will be used for the user who just verified.
            user_with_new_email.delete()

        return {}

    def handle_action_code(self, action_code: Code, **kwargs) -> None:
        action_code.change_user_email()
        self.action_code_model.objects.filter(user=action_code.user).delete()

    @extend_schema(
        summary='complete email change',
        request=None,
        parameters=[schemas.CodeQueryParameter],
        responses={
            200: OpenApiResponse(
                response=serializers.SuccessMessageSerializer,
                examples=[
                    OpenApiExample(
                        'Email change completed successfully',
                        value={'success': success_message},
                    ),
                ],
            ),
            400: schemas.ErrorCodeResponse,
        },
    )
    def post(self, request, format=None):
        """Confirm email change action.

        Updates the email field of the user related with the provided valid
        email change code.

        Note:
            After update, all email change codes related with the user are
            deleted.
        """
        return super().post(request, format)


class PasswordChange(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.PasswordChangeSerializer

    @extend_schema(
        summary='change user password',
        request=serializer_class,
        responses={
            200: OpenApiResponse(
                response=serializers.SuccessMessageSerializer,
                examples=[
                    OpenApiExample(
                        'Password change completed successfully',
                        value={'success': 'Password has been changed.'},
                    ),
                ],
            ),
            400: schemas.ErrorCodeResponse,
        }
    )
    def post(self, request, format=None):
        """Change the user password."""
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user

        if not user.check_password(serializer.data.get('password')):
            return Response({
                'detail': _(
                    'The given `password` field does not match with the '
                    'user password.',
                ),
            }, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.data.get('new_password'))
        user.save()

        return Response({
            'success': _('Password has been changed.'),
        }, status=status.HTTP_200_OK)


class Login(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = serializers.LoginSerializer

    def authenticate_user(
        self,
        serializer: serializers.LoginSerializer,
    ) -> USER:
        email = serializer.data.get('email')
        password = serializer.data.get('password')
        return authenticate(email=email, password=password)

    @extend_schema(
        summary='login',
        responses={
            200: OpenApiResponse(
                response=serializers.TokenSerializer,
                description='User authentication token',
            ),
            401: serializers.DetailErrorSerializer,
        }
    )
    def post(self, request, format=None):
        """Get or create the authentication token.

        Returns the authentication token for the user with provided
        credentials.
        """
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = self.authenticate_user(serializer)

        if not user:
            return Response({
                'detail': _('Unable to login with provided credentials.'),
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_verified:
            return Response({
                'detail': _('User account not verified.'),
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({
                'detail': _('User account not active.'),
            }, status=status.HTTP_401_UNAUTHORIZED)

        token, is_created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)


class Logout(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary='logout',
        request=None,
        parameters=[schemas.AuthorizationHeaderParameter],
        responses={
            200: OpenApiResponse(
                response=serializers.SuccessMessageSerializer,
                examples=[
                    OpenApiExample(
                        'Message about user logging out',
                        value={
                            'success': 'User logged out',
                        },
                    ),
                ],
            ),
        },
    )
    def post(self, request, format=None):
        """Logout user.

        Note:
            Deletes the user related authentication token.
        """
        tokens = Token.objects.filter(user=request.user)
        for token in tokens:
            token.delete()
        return Response({
            'success': _('User logged out.'),
        }, status=status.HTTP_200_OK)
