from typing import Optional, Callable, Any
from django.urls import reverse_lazy

from .typing import TemplateFiles, Context

from .utils import get_template_files, send_multi_format_email
from .settings import settings


class Email:
    def __init__(self, prefix: str, folder: str = "") -> None:
        self._prefix = prefix
        self._folder = folder
        self._templates: Optional[TemplateFiles] = None

    def __str__(self) -> str:
        return '%s [%s, %s]' % (
            self.__class__.__name__,
            self._folder,
            self._prefix,
        )

    @property
    def templates(self):
        if self._templates is not None:
            return self._templates

        self._templates = get_template_files(
            folder=self._folder,
            prefix=self._prefix,
        )
        return self._templates

    def get_send_email_callable(self) -> Callable[..., Any]:
        """Return the send email callable."""
        return send_multi_format_email

    def send_email(self, target: str, context: Context) -> None:
        self.get_send_email_callable()(
            context=context,
            target_email=target,

            templates=self.templates,
        )


class CodeVerifyEmail(Email):
    def __init__(
        self,
        *args,
        link_to_url: Optional[str] = None,
        **kwargs,
    ) -> None:
        # `link_to_url` is needed in case there is no client link and the
        # email should return the URL for specific view
        self.link_to_url = link_to_url

        super().__init__(*args, **kwargs)

    @property
    def _default_link(self):
        if hasattr(self, '_link'):
            return self._link

        self._link = (
            settings.USER_EMAILS_DEFAULT_ORIGIN
            + reverse_lazy(self.link_to_url)
        )

        return self._link

    def handle_context_link(self, context: Context) -> Context:
        # Return unchanged context if the `link_to_url` attribute is missing
        if not self.link_to_url:
            return context

        if context.get('link') is None:
            raise AttributeError(
                f'For {self} class the `link` context attribute is required.',
            )

        # replace context link with default link when it is empty
        context['link'] = context.get('link') or self._default_link
        return context

    def send_email(self, target: str, context: Context) -> None:
        context['code'] = 'CheckCode'
        return super().send_email(target, self.handle_context_link(context))
