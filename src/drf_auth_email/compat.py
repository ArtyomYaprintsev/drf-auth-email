try:
    from drf_spectacular.utils import \
        extend_schema, \
        extend_schema_view, \
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

    def create_empty_decorator(*args, **kwargs):
        """Return decorator without any logic."""
        def decorator(f):
            return f
        return decorator

    extend_schema = create_empty_decorator
    extend_schema_view = create_empty_decorator
