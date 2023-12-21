from django.urls import path

from . import views
from .settings import settings


pattern = settings.USER_EMAIL_URL_BASENAME + '-%s'

urlpatterns = [
    path(
        'signup/verify/code/',
        views.SignupCodeVerify.as_view(),
        name=pattern % 'signup-code-verify',
    ),
    path(
        'signup/verify/',
        views.SignupVerify.as_view(),
        name=pattern % 'signup-verify',
    ),
    path(
        'signup/',
        views.Signup.as_view(),
        name=pattern % 'signup',
    ),

    path(
        'password/reset/verify/code/',
        views.PasswordResetCodeVerify.as_view(),
        name=pattern % 'password-reset-code-verify',
    ),
    path(
        'password/reset/verify/',
        views.PasswordResetVerify.as_view(),
        name=pattern % 'password-reset-verify',
    ),
    path(
        'password/reset/',
        views.PasswordReset.as_view(),
        name=pattern % 'password-reset',
    ),

    path(
        'email/change/verify/code/',
        views.EmailChangeCodeVerify.as_view(),
        name=pattern % 'email-change-code-verify',
    ),
    path(
        'email/change/verify/',
        views.EmailChangeVerify.as_view(),
        name=pattern % 'email-change-verify',
    ),
    path(
        'email/change/',
        views.EmailChange.as_view(),
        name=pattern % 'email-change',
    ),

    path(
        'password/change/',
        views.PasswordChange.as_view(),
        name=pattern % 'password-change',
    ),

    path('login/', views.Login.as_view(), name=pattern % 'login'),
    path('logout/', views.Logout.as_view(), name=pattern % 'logout'),
]
