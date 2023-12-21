from .settings import settings


Email = settings.USER_EMAILS_CLASS
pattern = settings.USER_EMAIL_URL_BASENAME + '-%s'
AUTH_FOLDER = 'auth'


welcome_email = Email(
    prefix='welcome_email',
    folder=AUTH_FOLDER,
)
signup_email = Email(
    prefix='signup_email',
    folder=AUTH_FOLDER,
    link_to_url=pattern % 'signup-verify',
)
password_reset_email = Email(
    prefix='password_reset_email',
    folder=AUTH_FOLDER,
    link_to_url=pattern % 'password-reset-verify',
)
email_change_old_notify_email = Email(
    prefix='email_change_old_notify_email',
    folder=AUTH_FOLDER,
)
email_change_new_confirm_email = Email(
    prefix='email_change_new_confirm_email',
    folder=AUTH_FOLDER,
    link_to_url=pattern % 'email-change-verify',
)
