from typing import Any, NamedTuple


Context = dict[str, Any]
Kwargs = dict[str, Any]


class TemplateFiles(NamedTuple):
    """Keeps mail templates file paths."""

    subject: str
    txt: str
    html: str
