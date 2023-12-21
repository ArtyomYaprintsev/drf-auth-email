try:
    from drf_spectacular.utils import \
        extend_schema, \
        OpenApiResponse, \
        OpenApiParameter, \
        OpenApiExample
except ImportError:
    class BaseIgnoreClass:
        """Accept some init arguments and ignore it."""

        def __init__(self, *args, **kwargs) -> None:
            pass

    class OpenApiParameter(BaseIgnoreClass):
        """Ignored `drf_spectacular.utils.OpenApiParameter` class."""
        QUERY = None
        HEADER = None

    class OpenApiExample(BaseIgnoreClass):
        """Ignored `drf_spectacular.utils.OpenApiExample` class."""

    class OpenApiResponse(BaseIgnoreClass):
        """Ignored `drf_spectacular.utils.OpenApiResponse` class."""

    def extend_schema(*args, **kwargs):
        """Ignored `drf_spectacular.utils.extend_schema` method."""
        def decorator(f):
            return f
        return decorator
