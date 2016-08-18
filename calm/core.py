"""
Here lies the core of Calm.
"""
import re
from collections import defaultdict

from tornado.web import Application
from tornado.websocket import WebSocketHandler

from calm.ex import DefinitionError, ClientError
from calm.codec import ArgumentParser
from calm.service import CalmService
from calm.handler import (MainHandler, DefaultHandler, SwaggerHandler,
                          HandlerDef)

__all__ = ['CalmApp']


class CalmApp(object):
    """
    This class defines the Calm Application.

    Starts using calm by initializing an instance of this class. Afterwards,
    the application is being defined by calling its instance methods,
    decorators on your user-defined handlers.

    Public Methods:
        * configure - use this method to tweak some configuration parameter
                      of a Calm Application
        * get, post, put, delete - appropriate HTTP method decorators.
                                   The user defined handlers should be
                                   decorated by these decorators specifying
                                   the URL
        * service - creates a new Service using provided URL prefix
        * make_app - compiles the Calm application and returns a Tornado
                     Application instance
    """
    URI_REGEX = re.compile(r':([^\/\?:]*)')
    config = {  # The default configuration
        'argument_parser': ArgumentParser,
        'error_key': 'error',
        'swagger_url': '/swagger.json'
    }

    def __init__(self, name, version, *,
                 host=None, base_path=None,
                 description='', tos=''):
        super(CalmApp, self).__init__()

        self._app = None
        self._route_map = defaultdict(dict)
        self._custom_handlers = []
        self._ws_map = {}

        self.name = name
        self.version = version
        self.description = description
        self.tos = tos
        self.license = None
        self.contact = None
        self.host = host
        self.base_path = base_path

    def set_licence(self, name, url):
        """
        Set a License information for the API.

        Arguments:
            * name - The license name used for the API.
            * url - A URL to the license used for the API.
        """
        self.license = {
            'name': name,
            'url': url
        }

    def set_contact(self, name, url, email):
        """
        Set a contact information for the API.

        Arguments:
            * name - The identifying name of the contact person/organization.
            * url - The URL pointing to the contact information.
            * email - The email address of the contact person/organization.
        """
        self.contact = {
            'name': name,
            'url': url,
            'email': email
        }

    def configure(self, **kwargs):
        """
        Configures the Calm Application.

        Use this method to customize the Calm Application to your needs.
        """
        self.config.update(kwargs)

    def make_app(self):
        """Compiles and returns a Tornado Application instance."""
        route_defs = []

        default_handler_args = {
            'argument_parser': self.config.get('argument_parser',
                                               ArgumentParser),
            'app': self
        }

        for uri, methods in self._route_map.items():
            init_params = {
                **methods,  # noqa
                **default_handler_args  # noqa
            }

            route_defs.append(
                (self._regexify_uri(uri), MainHandler, init_params)
            )

        for url_spec in self._custom_handlers:
            route_defs.append(url_spec)

        for uri, handler in self._ws_map.items():
            route_defs.append(
                (self._regexify_uri(uri), handler)
            )

        route_defs.append(
            (self.config['swagger_url'],
             SwaggerHandler,
             default_handler_args)
        )

        self._app = Application(route_defs,
                                default_handler_class=DefaultHandler,
                                default_handler_args=default_handler_args)

        return self._app

    def add_handler(self, *url_spec):
        """Add a custom `RequestHandler` implementation to the app."""
        self._custom_handlers.append(url_spec)

    def custom_handler(self, *uri_fragments, init_args=None):
        """
        Decorator for custom handlers.

        A custom `RequestHandler` implementation decorated with this decorator
        will be added to the application with the specified `uri` and
        `init_args`.
        """
        def wrapper(klass):
            """Adds the `klass` as a custom handler and returns it back."""
            self.add_handler(self._normalize_uri(*uri_fragments),
                             klass,
                             init_args)

            return klass

        return wrapper

    @classmethod
    def _normalize_uri(cls, *uri_fragments):
        """Join the URI fragments and strip."""
        uri = '/'.join(
            u.strip('/') for u in uri_fragments
        )
        uri = '/' + uri

        return uri

    def _regexify_uri(self, uri):
        """Convert a URL pattern into a regex."""
        uri += '/?'
        path_params = self.URI_REGEX.findall(uri)
        for path_param in path_params:
            uri = uri.replace(
                ':{}'.format(path_param),
                r'(?P<{}>[^\/\?]*)'.format(path_param)
            )

        return uri

    def _add_route(self, http_method, function, *uri_fragments,
                   consumes=None, produces=None):
        """
        Maps a function to a specific URL and HTTP method.

        Arguments:
            * http_method - the HTTP method to map to
            * function - the handler function to be mapped to URL and method
            * uri - a list of URL fragments. This is used as a tuple for easy
                    implementation of the Service notion.
            * consumes - a Resource type of what the operation consumes
            * produces - a Resource type of what the operation produces
        """
        uri = self._normalize_uri(*uri_fragments)
        uri_regex = self._regexify_uri(uri)
        handler_def = HandlerDef(uri, uri_regex, function)

        consumes = getattr(function, 'consumes', consumes)
        produces = getattr(function, 'produces', produces)
        handler_def.consumes = consumes
        handler_def.produces = produces

        function.handler_def = handler_def
        self._route_map[uri][http_method.lower()] = handler_def

    def _decorator(self, http_method, *uri,
                   consumes=None, produces=None):
        """
        A generic HTTP method decorator.

        This method simply stores all the mapping information needed, and
        returns the original function.
        """
        def wrapper(function):
            """Takes a record of the function and returns it."""
            self._add_route(http_method, function, *uri,
                            consumes=consumes, produces=produces)
            return function

        return wrapper

    def get(self, *uri, consumes=None, produces=None):
        """Define GET handler for `uri`"""
        return self._decorator("GET", *uri,
                               consumes=consumes, produces=produces)

    def post(self, *uri, consumes=None, produces=None):
        """Define POST handler for `uri`"""
        return self._decorator("POST", *uri,
                               consumes=consumes, produces=produces)

    def delete(self, *uri, consumes=None, produces=None):
        """Define DELETE handler for `uri`"""
        return self._decorator("DELETE", *uri,
                               consumes=consumes, produces=produces)

    def put(self, *uri, consumes=None, produces=None):
        """Define PUT handler for `uri`"""
        return self._decorator("PUT", *uri,
                               consumes=consumes, produces=produces)

    def websocket(self, *uri_fragments):
        """Define a WebSocket handler for `uri`"""
        def decor(klass):
            """Takes a record of the WebSocket class and returns it."""
            if not isinstance(klass, type):
                raise DefinitionError("A WebSocket handler should be a class")
            elif not issubclass(klass, WebSocketHandler):
                name = getattr(klass, '__name__', 'WebSocket handler')
                raise DefinitionError(
                    "{} should subclass '{}'".format(name,
                                                     WebSocketHandler.__name__)
                )

            uri = self._normalize_uri(*uri_fragments)
            self._ws_map[uri] = klass

            return klass

        return decor

    def service(self, url):
        """Returns a Service defined by the `url` prefix"""
        return CalmService(self, url)

    def generate_swagger_json(self):
        # TODO: call this once during init
        """Generates the swagger.json contents for the Calm Application."""
        info = {
            'title': self.name,
            'version': self.version,
        }

        if self.description:
            info['description'] = self.description
        if self.tos:
            info['termsOfService'] = self.tos
        if self.contact:
            info['contact'] = self.contact
        if self.license:
            info['license'] = self.license

        swagger_json = {
            'swagger': '2.0',
            'info': info,
            'consumes': ['application/json'],
            'produces': ['application/json'],
            # 'definitions': {},  # get from Resource
            # 'paths': {},  # get from Application
        }

        if self.host:
            swagger_json['host'] = self.host
        if self.base_path:
            swagger_json['basePath'] = self.base_path

        defined_errors = ClientError.get_defined_errors()
        response_definitions = {
            e.__name__: self._generate_error_definition(e)
            for e in defined_errors
        }
        if response_definitions:
            swagger_json['responses'] = response_definitions

        paths = defaultdict(dict)
        for uri, methods in self._route_map.items():
            for method, hdef in methods.items():
                paths[uri][method] = hdef.operation_definition

        if paths:
            swagger_json['paths'] = paths

        return swagger_json

    @classmethod
    def _generate_error_definition(cls, error):
        return {
            'description': error.__doc__,
            'schema': {
                '$ref': '#/definitions/Error'
            }
        }

    def _generate_error_schema(self):
        return {
            'Error': {
                'properties': {
                    self.config['error_key']: {'type': 'string'}
                },
                'required': [self.config['error_key']]
            }
        }
