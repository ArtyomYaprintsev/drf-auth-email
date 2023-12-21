from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DrfAuthEmailConfig(AppConfig):
    name = 'drf_auth_email'
    verbose_name = _('django-auth-email')
