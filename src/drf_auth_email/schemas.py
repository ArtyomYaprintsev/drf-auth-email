from .compat import OpenApiParameter, OpenApiExample, OpenApiResponse
from .serializers import DetailErrorSerializer


CodeQueryParameter = OpenApiParameter(
    name='code',
    type=str,
    location=OpenApiParameter.QUERY,
    description='Action code',
    required=True,
)
"""TODO: add docs."""


AuthorizationHeaderParameter = OpenApiParameter(
    name='authorization',
    type=str,
    location=OpenApiParameter.HEADER,
    description='Authorization token',
    required=True,
)
"""TODO: add docs."""


ErrorCodeResponse = OpenApiResponse(
    response=DetailErrorSerializer,
    description='Action code is invalid',
    examples=[
        OpenApiExample(
            'Code parameter is missing',
            description='string `code` parameter is missing',
            value={
                'detail': (
                    'The `code` attribute must be a non-empty '
                    'string.'
                ),
            },
        ),
        OpenApiExample(
            'Code parameter is invalid',
            description=(
                'could not find a model that related with '
                'provided code'
            ),
            value={
                'detail': 'The given `code` parameter is invalid.',
            },
        ),
        OpenApiExample(
            'Code is expired',
            description='code is expired',
            value={
                'detail': 'The given `code` parameter is expired.',
            },
        ),
    ],
)
"""TODO: add docs."""
