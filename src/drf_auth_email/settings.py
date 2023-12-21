from typing import Any

from django.conf import settings as django_settings
from django.test.signals import setting_changed
from django.utils.module_loading import import_string


DEFAULTS = {
    'USER_EMAILS_CLASS': 'drf_auth_email.email.CodeVerifyEmail',
    'USER_EMAILS_WELCOME': 'drf_auth_email.emails.welcome_email',
    'USER_EMAILS_SIGNUP': 'drf_auth_email.emails.signup_email',
    'USER_EMAILS_PASSWORD_RESET': 'drf_auth_email.emails.password_reset_email',
    'USER_EMAILS_EMAIL_CHANGE_OLD_NOTIFY': 'drf_auth_email.emails.email_change_old_notify_email',
    'USER_EMAILS_EMAIL_CHANGE_NEW_CONFIRM': 'drf_auth_email.emails.email_change_new_confirm_email',

    'USER_EMAILS_DEFAULT_ORIGIN': 'http://127.0.0.1:8000',
    'USER_EMAIL_URL_BASENAME': 'drf-auth-email',

    # In seconds
    'USER_CODE_VERIFY_EXPIRE_TIME': 259200
}


# Settings with dot notation
IMPORT_STRINGS = [
    'USER_EMAILS_CLASS',
    'USER_EMAILS_WELCOME',
    'USER_EMAILS_SIGNUP',
    'USER_EMAILS_PASSWORD_RESET',
    'USER_EMAILS_EMAIL_CHANGE_OLD_NOTIFY',
    'USER_EMAILS_EMAIL_CHANGE_NEW_CONFIRM',
]


class CachedSettings:
    def __init__(self) -> None:
        self._cached = {}

    def __getattr__(self, __name: str) -> Any:
        if __name not in DEFAULTS:
            raise AttributeError('Invalid setting: %s' % __name)

        if __name in self._cached:
            return self._cached[__name]

        attr = getattr(django_settings, __name, DEFAULTS[__name])

        if __name in IMPORT_STRINGS:
            attr = import_string(attr)

        self._cached[__name] = attr
        return attr

    def reload(self):
        self._cached = {}


settings = CachedSettings()


def reload_settings(*args, **kwargs):
    settings.reload()


setting_changed.connect(reload_settings)
