import binascii
import os

from typing import Optional
from datetime import timedelta

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser as BaseAbstractUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .typing import Context
from .email import Email
from .managers import UserManager

from .settings import settings


class AbstractUser(BaseAbstractUser):
    username_validator = None
    username = None

    email = models.EmailField(
        _('email address'),
        max_length=255,
        unique=True,
        error_messages={
            'unique': _('A user with that email address already exists.'),
        }
    )

    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_(
            'Designates whether this user has completed the email '
            'verification process to allow login.',
        ),
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        abstract = True

    def __str__(self):
        return self.email


class AbstractCodeVerify(models.Model):
    """Docs."""

    code = models.CharField(
        _('code'),
        max_length=40,
        primary_key=True,
        editable=False,
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        verbose_name=_('user'),
    )
    ipaddr = models.GenericIPAddressField(_('ip address'))
    link = models.URLField(
        _('email link'),
        blank=True, default='',
        help_text=_(
            'Contains a link to some source, will be supplemented with a '
            'request parameter with an instance code inside email.',
        )
    )

    created = models.DateTimeField(_('date created'), auto_now_add=True)

    email: Email | None = None
    expire_time: timedelta | None = timedelta(
        seconds=settings.USER_CODE_VERIFY_EXPIRE_TIME,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        return super().save(*args, **kwargs)

    @classmethod
    def generate_code(cls):
        return binascii.hexlify(os.urandom(20)).decode()

    @classmethod
    def check_is_valid(cls, code: str, select_related_user: bool = False):
        if not isinstance(code, str) or not code:
            raise ValueError(
                _('The `code` attribute must be a non-empty string.'),
            )

        # Safe method to get instance by code
        queryset = cls.objects.filter(code=code)

        if select_related_user:
            queryset = queryset.select_related('user')

        instance = queryset.first()

        if instance is None:
            raise ValueError(_('The given `code` parameter is invalid.'))

        if instance.is_expired():
            raise ValueError(_('The given `code` parameter is expired.'))

        return instance

    def __str__(self):
        return self.code

    def _default_context(self) -> dict[str, str]:
        return {
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'code': self.code,
            'link': self.link,
            'ipaddr': self.ipaddr,
        }

    def get_email(self) -> Email:
        assert self.email, (
            'The %s class `email` attribute was not provided.'
            % self.__class__.__name__,
        )
        return self.email

    def is_expired(self):
        if self.expire_time is None:
            return False

        return timezone.now() - self.created > self.expire_time

    def send_email(self, context: Optional[Context] = None):
        context = self._default_context() | ({} if context is None else context)
        self.get_email().send_email(target=self.user.email, context=context)
