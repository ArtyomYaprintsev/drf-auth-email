from typing import Any

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings as django_settings

from .settings import settings
from .abstracts import AbstractCodeVerify


ABSTRACT = 'drf_auth_email' not in django_settings.INSTALLED_APPS


class SignupCode(AbstractCodeVerify):
    email = settings.USER_EMAILS_SIGNUP

    class Meta:
        verbose_name = _('signup code')
        verbose_name_plural = _('signup codes')
        abstract = ABSTRACT

    def verify_user(self) -> None:
        self.user.is_verified = True
        self.user.save()


class PasswordResetCode(AbstractCodeVerify):
    email = settings.USER_EMAILS_PASSWORD_RESET

    class Meta:
        verbose_name = _('password reset code')
        verbose_name_plural = _('password reset codes')
        abstract = ABSTRACT

    def change_user_password(self, password: str):
        self.user.set_password(password)
        self.user.save()


class EmailChangeCode(AbstractCodeVerify):
    new_email = models.EmailField(
        _('new email address'),
        max_length=255,
        help_text=_(
            'New email address will be related with user after email change '
            'verification.',
        )
    )

    class Meta:
        verbose_name = _('email change code')
        verbose_name_plural = _('email change codes')
        abstract = ABSTRACT

    def send_email(self, context: dict[str, Any] | None = None):
        context = (
            self._default_context()
            | ({} if context is None else context)
        )

        # send notification to old email address
        settings.USER_EMAILS_EMAIL_CHANGE_OLD_NOTIFY.send_email(
            target=self.user.email,
            context=context,
        )
        # send confirmation to new email address
        settings.USER_EMAILS_EMAIL_CHANGE_NEW_CONFIRM.send_email(
            target=self.new_email,
            context=context
        )

    def change_user_email(self):
        self.user.email = self.new_email
        self.user.save()
