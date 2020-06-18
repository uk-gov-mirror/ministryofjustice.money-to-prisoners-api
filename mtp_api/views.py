from django.conf import settings
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import permissions
from rest_framework.request import clone_request
from rest_framework.schemas import SchemaGenerator


class CustomOpenAPISchemaGenerator(OpenAPISchemaGenerator):

    def __init__(self, info, version='', url=None, patterns=None, urlconf=None):
        super().__init__(info, version, url, patterns, urlconf)
        self._gen = CustomActionSchemaGenerator(info.title, url, info.get('description', ''), patterns, urlconf)


schema_view = get_schema_view(
    info=openapi.Info(
        title='Prisoner Money API',
        default_version='v1',
        description='Prisoner Money API',
        terms_of_service=f'{settings.SEND_MONEY_URL}/en-gb/terms/',
        contact=openapi.Contact(email=settings.TEAM_EMAIL),
        license=openapi.License(name='MIT License'),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    generator_class=CustomOpenAPISchemaGenerator,
    authentication_classes=(OAuth2Authentication,)
)


class CustomActionSchemaGenerator(SchemaGenerator):
    """
    The reason for subclassing the default Django Rest Framework
    SchemaGenerator class is that the APIView class does not populate
    the `actions` attribute on the return value of the `as_view` method,
    instead assigning any kwargs used in `as_view` to the `initkwargs`
    attribute.

    This means that when the SchemaGenerator introspects the generator
    returned from the function wrapper generated by the
    `django.conf.urls.url()` invocation, it looks for a view.actions attribute
    only and errors if `action_map` is set to the default value of `None` by
    `SchemaGenerator().create_view()`
    """

    def __init__(self, title=None, url=None, description=None, patterns=None, urlconf=None):
        super().__init__(title, url, description, patterns, urlconf)
        # For some reason the generator class does not handle the case where the first argument
        # is an OpenAPI.Info object containing all the necessary metadata instead of a string.
        # So we handle this in the subclass
        if isinstance(title, openapi.Info):
            self.title = title.title
            if not self.description:
                self.description = title.description

    def create_view(self, callback, method, request=None):
        """
        Given a callback, return an actual view instance.
        """
        view = callback.cls(**getattr(callback, 'initkwargs', {}))
        view.args = ()
        view.kwargs = {}
        view.format_kwarg = None
        view.request = None

        actions = (
            getattr(callback, 'actions', None)
            or getattr(callback, 'initkwargs', {}).get('actions')
        )
        view.action_map = actions

        if actions is not None:
            if method == 'OPTIONS':
                view.action = 'metadata'
            else:
                view.action = actions.get(method.lower())

        if request is not None:
            view.request = clone_request(request, method)

        return view
