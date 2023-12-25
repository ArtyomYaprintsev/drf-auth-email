# drf-auth-email

[![PyPI - Version](https://img.shields.io/pypi/v/drf-auth-email.svg)](https://pypi.org/project/drf-auth-email)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/drf-auth-email.svg)](https://pypi.org/project/drf-auth-email)

User authentication and signup functionality for DRF via email addresses.

-----

## Table of Contents

- [Description](#description)
- [Installation](#installation)
- [Usage](#usage)
  - [Custom email template](#custom-email-template)
  - [Custom email](#custom-email)
  - [Celery usage](#celery-usage)
- [Roadmap](#roadmap)
- [License](#license)

## Description

`drf-auth-email` provides API endpoints for user signup and authentication and user credential management such as email change, password reset and change. A field with the user's email address is required to send messages with a registration confirmation code e.g.

The project idea based on [django-rest-authemail](https://github.com/celiao/django-rest-authemail) repository, but designed to be more flexible and RESTful.

## Installation

```console
pip install drf-auth-email
```

### Requirements

Requirements

## Usage

1. Create your user model

    ```python
    from drf_auth_email.abstracts import AbstractUser

    class MyUser(AbstractUser):
        class Meta(AbstractUser.Meta):
            swappable = 'AUTH_USER_MODEL'
            abstract = False
    ```

    Note:  `drf-auth-email.AbstractUser` model based on the Django `AbstractUser` class.

2. Config your project with `drf-auth-email` usage and specify your model using the `AUTH_USER_MODEL` setting

    ```python
    INSTALLED_APPS = [
        ...
        'rest_framework',
        'rest_framework.authtoken',
        'drf_auth_email',

        'myapp',
        ...
    ]

    AUTH_USER_MODEL = 'myapp.MyUser'
    ```

3. Include `drf-auth-email` urls

    ```python
    from django.urls import include, path
    
    urlpatterns = [
        ...
        path('auth/', include('drf_auth_email.urls')),
        ...
    ]
    ```

4. Make and run migrations

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5. Run server

    ```bash
    python manage.py runserver
    ```

> [!WARNING]
> Do not forget to config email sending, more information [here](https://docs.djangoproject.com/en/stable/topics/email/).

### Custom email template

1. Create custom email template.

    The email template should consist of:
    - `{email_prefix}_subject.txt` file with email subject
    - `{email_prefix}.html` file with email html template
    - `{email_prefix}.txt` file with email template text

    Example inside `/templates/myapp/` directory:

    ```txt
    # /templates/myapp/my_welcome_email_subject.txt

    My Welcome Email
    ```

    ```html
    # /templates/myapp/my_welcome_email.html

    <!DOCTYPE html>
    <html lang="en-US">
    <head>
        <meta charset="UTF-8" />
        <title>My Welcome Email</title>
    </head>
    <body>
        <p>Your registration is complete.</p>
        <p>Custom email received.</p>
    </body>
    </html>
    ```

    ```txt
    # /templates/myapp/my_welcome_email.txt

    Your registration is complete.
    Custom email received.
    ```

2. Create new `Email` class instance inside `myapp/emails.py` file

    ```python
    from drf_auth_email.emails import Email

    my_welcome_email = Email(
        prefix='my_welcome_email',
        folder='myapp',
    )
    ```

3. Specify your welcome email template using the `USER_EMAILS_WELCOME` setting

    ```python
    USER_EMAILS_WELCOME = 'myapp.emails.my_welcome_email'
    ```

### Custom email

To create custom email repeat 1-2 steps from [custom email template](#custom-email-template) and call the `send_email()` method of the created `Email` instance.

```python
from myapp.emails import my_welcome_email


my_welcome_email.send_email(
    target='example@email.com',
    context={'foo': 'bar'},
)
```

### Celery usage

Email sending through [Celery](https://docs.celeryq.dev/en/stable/django/) library

1. Config `Celery` usage

    ```python
    # myproject/settings.py

    # Celery settings
    # https://docs.celeryq.dev/en/stable/userguide/configuration.html

    CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
    CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
    ```

    ```python
    # myproject/celery.app

    import os
    from celery import Celery

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    app = Celery("config")
    app.config_from_object("django.conf:settings", namespace="CELERY")

    app.autodiscover_tasks()
    ```

2. Create `Celery` task

    ```python
    # myproject/tasks.py

    from drf_auth_email.utils import send_multi_format_email

    from myproject.celery import app

    send_email_task = app.task()(send_multi_format_email)
    ```

3. Create custom `Email` class

    ```python
    # myproject/email.py

    from drf_auth_email.email import CodeVerifyEmail

    from myproject.tasks import send_email_task


    class TaskEmail(CodeVerifyEmail):
        def get_send_email_callable(self):
            return send_email_task.delay
    ```

4. Specify your email class using the `USER_EMAILS_CLASS` setting

    ```python
    USER_EMAILS_CLASS = 'myproject.email.TaskEmail'
    ```

## API endpoints

API endpoints described inside the `drf_auth_email.views`, you can check full API scheme inside [openapi.json](https://github.com/ArtyomYaprintsev/drf-auth-email/blob/master/openapi.md) file

Endpoints summary:

- `Signup`: create user signup request (user should to verify email to complete signup action)
- `SignupVerifyCode`: verify user signup code
- `SignupVerify`: verify user email and complete signup action
- `PasswordReset`: create user password reset request (user should to click on link inside received email message to complete password reset action)
- `PasswordResetVerifyCode`: verify user password reset code
- `PasswordResetVerify`: complete password reset action
- `EmailChange`: create user email change request (user should to click on link inside received email message to complete email change action)
- `EmailChangeVerifyCode`: verify email change code
- `EmailChangeVerify`: complete email change action
- `PasswordChange`: change user password field
- `Login`: user login
- `Logout`: user logout

## Roadmap

- [ ] Create admin models
- [ ] Add docstrings
- [ ] Add tests
- [ ] Describe `Email.link_to_url` attribute inside the `README` file
- [ ] Describe template context for each email type inside the `README` file

## License

`drf-auth-email` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
