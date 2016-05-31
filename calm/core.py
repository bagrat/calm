"""
Here lies the core of Calm.
"""
import re
import inspect
from collections import defaultdict

from tornado.web import Application

from calm.ex import DefinitionError
from calm.codec import ArgumentParser
from calm.service import CalmService
from calm.handler import MainHandler, DefaultHandler

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
        'plain_result_key': 'result',
        'error_key': 'error'
    }

    def __init__(self):
        super(CalmApp, self).__init__()

        self._app = None
        self._route_map = defaultdict(dict)

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
                (uri, MainHandler, init_params)
            )

        self._app = Application(route_defs,
                                default_handler_class=DefaultHandler,
                                default_handler_args=default_handler_args)

        return self._app

    def _normalize_uri(self, *uri_fragments):
        """Convert colon-uri into a regex."""
        uri = '/'.join(
            u.strip('/') for u in uri_fragments
        )
        uri = '/' + uri + '/?'

        path_params = self.URI_REGEX.findall(uri)
        for path_param in path_params:
            uri = uri.replace(
                ':{}'.format(path_param),
                r'(?P<{}>[^\/\?]*)'.format(path_param)
            )

        return uri

    @classmethod
    def _get_path_params(cls, uri, argspec):
        """Extract path arguments from the URI."""
        regex = re.compile(uri)
        path_params = list(regex.groupindex.keys())

        function, _, required_args, optional_args, has_kwargs = argspec

        result = {}
        for path_param in path_params:
            if path_param in optional_args:
                raise DefinitionError(
                    "Path asrgument '{}' must not be optional in '{}'".format(
                        path_param,
                        function.__name__
                    )
                )
            elif not has_kwargs and path_param not in required_args:
                raise DefinitionError(
                    "Path argument '{}' must be expected by '{}'".format(
                        path_param,
                        function.__name__
                    )
                )
            else:
                result[path_param] = {
                    'type': 'path',
                    'required': True
                }

        return result

    @classmethod
    def _get_query_params(cls, argspec, path_params):
        """Determine and return query arguments."""
        _, all_args, required_args, _, _ = argspec

        return {
            param: {
                'type': 'query',
                'required': param in required_args
            } for param in all_args if param not in path_params
        }

    @classmethod
    def _get_function_args(cls, function):
        """Get function signature in groups."""
        # TODO: switch to using `inspect.signature()`
        argspec = inspect.getfullargspec(function)
        all_args = argspec.args[1:]
        has_kwargs = argspec.varkw
        default_count = len(argspec.defaults or [])
        if default_count:
            required_args = all_args[:-default_count]
            optional_args = all_args[-default_count:]
        else:
            required_args = all_args
            optional_args = []

        return function, all_args, required_args, optional_args, has_kwargs

    def _get_request_arguments(self, uri, function):
        """Get request argument specification."""
        argspec = self._get_function_args(function)
        path_params = self._get_path_params(uri, argspec)
        query_params = self._get_query_params(argspec,
                                              path_params)

        return {
            **path_params,
            **query_params
        }

    def _add_route(self, http_method, function, *uri_fragments):
        """
        Maps a function to a specific URL and HTTP method.

        Arguments:
            * http_method - the HTTP method to map to
            * function - the handler function to be mapped to URL and method
            * uri - a list of URL fragments. This is used as a tuple for easy
                    implementation of the Service notion.
        """
        uri = self._normalize_uri(*uri_fragments)
        arguments = self._get_request_arguments(uri, function)

        handler_def = {
            'function': function,
            'arguments': arguments
        }

        self._route_map[uri][http_method.lower()] = handler_def

    def _decorator(self, http_method, *uri, **kwargs):
        """
        A generic HTTP method decorator.

        This method simply stores all the mapping information needed, and
        returns the original function.
        """
        def wrapper(function):
            """Takes a record of the function and returns it."""
            self._add_route(http_method, function, *uri, **kwargs)
            return function

        return wrapper

    def get(self, *uri):
        """Define GET handler for `uri`"""
        return self._decorator("GET", *uri)

    def post(self, *uri):
        """Define POST handler for `uri`"""
        return self._decorator("POST", *uri)

    def delete(self, *uri):
        """Define DELETE handler for `uri`"""
        return self._decorator("DELETE", *uri)

    def put(self, *uri):
        """Define PUT handler for `uri`"""
        return self._decorator("PUT", *uri)

    def service(self, url):
        """Returns a Service defined by the `url` prefix"""
        return CalmService(self, url)
