from typing import Optional

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from .typing import TemplateFiles, Context


def get_template_files(folder: str, prefix: str) -> TemplateFiles:
    """Get mail templates file paths by folder and prefix."""
    return TemplateFiles(
        '%s/%s_subject.txt' % (folder, prefix),
        '%s/%s.txt' % (folder, prefix),
        '%s/%s.html' % (folder, prefix),
    )


def send_multi_format_email(
    context: Context,
    target_email: str,
    folder: str = '',
    prefix: Optional[str] = None,
    templates: Optional[TemplateFiles] = None,
):
    _templates: TemplateFiles = None

    if templates is None and prefix is None:
        raise ValueError(
            'Can not to send multi-format email without template, specify '
            '`templates` or `prefix` attributes',
        )

    # Use `templates` attribute if this is not None
    if templates is not None:
        if isinstance(templates, TemplateFiles):
            _templates = templates

        # Necessary for some cases, for example when using Celery tasks, it
        # converts a 'TemplateFails' type variable into a regular `list`
        _templates = TemplateFiles(*templates)

    # Get templates using prefix and folder if `_templates` is None yet
    if _templates is None:
        _templates = get_template_files(folder, prefix)

    # Raise error if `_templates` variable can not be specified
    if _templates is None:
        # TODO: add folder, prefix and templates print
        raise ValueError(
            'Can not to specify templates to send multi-format email, check '
            'the given attributes.'
        )

    # Get attrs from settings
    from_email = settings.EMAIL_FROM
    to = target_email
    bcc_email = settings.EMAIL_BCC

    # Render templates with given context
    subject = render_to_string(_templates.subject).strip()
    text_content = render_to_string(_templates.txt, context)
    html_content = render_to_string(_templates.html, context)

    msg = EmailMultiAlternatives(
        subject, text_content,
        # Can be customized
        from_email, [to], bcc=[bcc_email],
    )
    msg.attach_alternative(html_content, 'text/html')
    msg.send()
