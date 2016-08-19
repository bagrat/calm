"""
This module extends and defines Torndo RequestHandlers.

Classes:
    * MainHandler - this is the main RequestHandler subclass, that is mapped to
                    all URIs and serves as a dispatcher handler.
    * DefaultHandler - this class serves all the URIs that are not defined
                       within the application, returning `404` error.
"""
import re
import json
import inspect
from inspect import Parameter
import logging
import datetime

from tornado.web import RequestHandler
from tornado.web import MissingArgumentError
from untt.util import parse_docstring

from calm.ex import (ServerError, ClientError, BadRequestError,
                     MethodNotAllowedError, NotFoundError, DefinitionError)
from calm.codec import ParameterJsonType

__all__ = ['MainHandler', 'DefaultHandler']


class MainHandler(RequestHandler):
    """
    The main dispatcher request handler.

    This class extends the Tornado `RequestHandler` class, and it is mapped to
    all the defined applications handlers handlers. This class implements all
    HTTP method handlers, which dispatch the control to the appropriate user
    handlers based on their definitions and request itself.
    """
    BUILTIN_TYPES = (str, list, tuple, set, int, float, datetime.datetime)

    def __init__(self, *args, **kwargs):
        """
        Initializes the dispatcher request handler.

        Arguments:
            * get, post, put, delete - appropriate HTTP method handler for
                                       a specific URI
            * argument_parser - a `calm.ArgumentParser` subclass
            * app - the Calm application
        """
        self._get_handler = kwargs.pop('get', None)
        self._post_handler = kwargs.pop('post', None)
        self._put_handler = kwargs.pop('put', None)
        self._delete_handler = kwargs.pop('delete', None)

        self._argument_parser = kwargs.pop('argument_parser')()
        self._app = kwargs.pop('app')

        self.log = logging.getLogger('calm')

        super(MainHandler, self).__init__(*args, **kwargs)

    def _get_query_args(self, handler_def):
        """Retreives the values for query arguments."""
        query_args = {}
        for qarg, definition in handler_def.query_args.items():
            is_required = definition['required']
            try:
                query_args[qarg] = self.get_query_argument(qarg)
            except MissingArgumentError:
                if not is_required:
                    continue

                raise BadRequestError(
                    "Missing required query argument '{}'".format(qarg)
                )

        return query_args

    def _cast_args(self, handler, args):
        """Converts the request arguments to appropriate types."""
        arg_types = handler.__annotations__
        for arg in args:
            arg_type = arg_types.get(arg)

            if not arg_type:
                continue

            args[arg] = self._argument_parser.parse(arg_type, args[arg])

    def _parse_and_update_body(self):
        """Parses the request body to JSON."""
        if self.request.body:
            try:
                json_body = json.loads(self.request.body.decode('utf-8'))
                self.request.body = json_body
            except json.JSONDecodeError:
                raise BadRequestError(
                    "Malformed request body. JSON is expected."
                )

    async def _handle_request(self, handler_def, **kwargs):
        """A generic HTTP method handler."""
        if not handler_def:
            raise MethodNotAllowedError()

        handler = handler_def.handler
        kwargs.update(self._get_query_args(handler_def))
        self._cast_args(handler, kwargs)
        self._parse_and_update_body()
        if inspect.iscoroutinefunction(handler):
            resp = await handler(self.request, **kwargs)
        else:
            self.log.warning("'%s' is not a coroutine!", handler_def.handler)
            resp = handler(self.request, **kwargs)

        self._write_response(resp)

    async def get(self, **kwargs):
        """The HTTP GET handler."""
        await self._handle_request(self._get_handler, **kwargs)

    async def post(self, **kwargs):
        """The HTTP POST handler."""
        await self._handle_request(self._post_handler, **kwargs)

    async def put(self, **kwargs):
        """The HTTP PUT handler."""
        await self._handle_request(self._put_handler, **kwargs)

    async def delete(self, **kwargs):
        """The HTTP DELETE handler."""
        await self._handle_request(self._delete_handler, **kwargs)

    def _write_response(self, response):
        """Converts various types to JSON and returns to the client"""
        if hasattr(response, '__json__'):
            result = response.__json__()
        else:
            result = response

        try:
            json_str = json.dumps(result)
        except TypeError:
            raise ServerError(
                "Could not serialize '{}' to JSON".format(
                    type(response).__name__
                )
            )

        self.set_header('Content-Type', 'application/json')
        self.write(json_str)
        self.finish()

    def write_error(self, status_code, exc_info=None, **kwargs):
        """The top function for writing errors"""
        if exc_info:
            exc_type, exc_inst, _ = exc_info
            if issubclass(exc_type, ClientError):
                self._write_client_error(exc_inst)
                return

        self._write_server_error()

    def _write_client_error(self, exc):
        """Formats and returns a client error to the client"""
        result = {
            self._app.config['error_key']: exc.message or str(exc)
        }

        self.set_status(exc.code)
        self.write(json.dumps(result))

    def _write_server_error(self):
        """Formats and returns a server error to the client"""
        result = {
            self._app.config['error_key']: 'Oops our bad. '
                                           'We are working to fix this!'
        }

        self.set_status(500)
        self.write(json.dumps(result))

    def data_received(self, data):  # pragma: no cover
        """This is to ommit quality check errors."""
        pass


class DefaultHandler(MainHandler):
    """
    This class extends the main dispatcher class for request handlers
    `MainHandler`.

    It implements the `_handle_request` method and raises `NotFoundError` which
    will be returned to the user as an appropriate JSON message.
    """
    async def _handle_request(self, *_, **dummy):
        raise NotFoundError()


class HandlerDef(object):
    """
    Defines a request handler.

    During initialization, the instance will process and store all argument
    information.
    """
    URI_REGEX = re.compile(r':([^\/\?:]*)')

    def __init__(self, uri, uri_regex, handler):
        super(HandlerDef, self).__init__()

        self.uri = uri
        self.uri_regex = uri_regex
        self.handler = handler
        self._signature = inspect.signature(handler)
        self._params = {
            k: v for k, v in list(
                self._signature.parameters.items()
            )[1:]
        }

        self.path_args = []
        self.query_args = {}

        self.consumes = getattr(handler, 'consumes', None)
        self.produces = getattr(handler, 'produces', None)

        self._extract_arguments()
        self.operation_definition = self._generate_operation_definition()

    def _extract_path_args(self):
        """Extracts path arguments from the URI."""
        regex = re.compile(self.uri_regex)
        self.path_args = list(regex.groupindex.keys())

        for path_arg in self.path_args:
            if path_arg in self._params:
                if self._params[path_arg].default is not Parameter.empty:
                    raise DefinitionError(
                        "Path argument '{}' must not be optional in '{}'"
                        .format(
                            path_arg,
                            self.handler.__name__
                        )
                    )
            else:
                raise DefinitionError(
                    "Path argument '{}' must be expected by '{}'".format(
                        path_arg,
                        self.handler.__name__
                    )
                )

    def _extract_query_arguments(self):
        """
        Extracts query arguments from handler signature

        Should be called after path arguments are extracted.
        """
        for _, param in self._params.items():
            if param.name not in self.path_args:
                python_type = (param.annotation
                               if param.annotation is not Parameter.empty
                               else str)
                try:
                    json_type = ParameterJsonType.from_python_type(
                        python_type
                    )
                except TypeError as ex:
                    raise DefinitionError(
                        "Wrong argument type for '{}'".format(param.name)
                    ) from ex

                self.query_args[param.name] = {
                    'required': param.default is Parameter.empty,
                    'type': python_type,
                    'json_type': json_type,
                    'default': (param.default
                                if param.default is not Parameter.empty
                                else None)
                }

    def _extract_arguments(self):
        """Extracts path and query arguments."""
        self._extract_path_args()
        self._extract_query_arguments()

    def _generate_operation_definition(self):
        summary, description = parse_docstring(self.handler.__doc__ or '')

        operation_id = '.'.join(
            [self.handler.__module__, self.handler.__name__]
        ).replace('.', '_')

        parameters = []
        for name in self.path_args:
            parameters.append({
                'name': name,
                'in': 'path',
                'required': True,
                'type': 'string'
                # TODO: add param description
            })

        for name, definition in self.query_args.items():
            param = {
                'name': name,
                'in': 'query',
                'required': definition['required'],
            }

            param_type = ParameterJsonType.from_python_type(definition['type'])
            param['type'] = param_type
            if param_type == 'array':
                param['items'] = param_type.params['items']

            if definition['default']:
                param['default'] = definition['default']
            parameters.append(param)

        if self.consumes:
            parameters.append({
                'in': 'body',
                'schema': self.consumes.json_schema
            })

        responses = {}
        if self.produces:
            responses['200'] = self.produces.json_schema
            # TODO: add error definition

        return {
            'summary': summary,
            'description': description,
            'operationId': operation_id,
            'parameters': parameters,
            'responses': responses
        }
        # TODO: add deprecated indicator


class SwaggerHandler(DefaultHandler):
    """
    The handler for Swagger.io (OpenAPI).

    This handler defined the GET method to output the Swagger.io (OpenAPI)
    definition for the Calm Application.
    """
    async def get(self):
        self._write_response(self._app.swagger_json)
