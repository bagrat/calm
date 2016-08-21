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
from untt.ex import ValidationError

from calm.ex import (ServerError, ClientError, BadRequestError,
                     MethodNotAllowedError, NotFoundError, DefinitionError)
from calm.param import QueryParam, PathParam

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
        for qarg in handler_def.query_args:
            try:
                query_args[qarg.name] = self.get_query_argument(qarg.name)
            except MissingArgumentError:
                if not qarg.required:
                    continue

                raise BadRequestError(
                    "Missing required query argument '{}'".format(qarg.name)
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

    def _parse_and_update_body(self, handler_def):
        """Parses the request body to JSON."""
        if self.request.body:
            try:
                json_body = json.loads(self.request.body.decode('utf-8'))
            except json.JSONDecodeError:
                raise BadRequestError(
                    "Malformed request body. JSON is expected."
                )

            new_body = json_body
            if handler_def.consumes:
                try:
                    new_body = handler_def.consumes.from_json(json_body)
                except ValidationError:
                    # TODO: log warning or error
                    raise BadRequestError("Bad data structure.")

            self.request.body = new_body

    async def _handle_request(self, handler_def, **kwargs):
        """A generic HTTP method handler."""
        if not handler_def:
            raise MethodNotAllowedError()

        handler = handler_def.handler
        kwargs.update(self._get_query_args(handler_def))
        self._cast_args(handler, kwargs)
        self._parse_and_update_body(handler_def)
        if inspect.iscoroutinefunction(handler):
            resp = await handler(self.request, **kwargs)
        else:
            self.log.warning("'%s' is not a coroutine!", handler_def.handler)
            resp = handler(self.request, **kwargs)

        if resp:
            self._write_response(resp, handler_def)

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

    def _write_response(self, response, handler_def=None):
        """Converts various types to JSON and returns to the client"""
        result = response
        if hasattr(response, '__json__'):
            result = response.__json__()

        if handler_def and handler_def.produces:
            try:
                handler_def.produces.validate(result)
            except ValidationError:
                self.log.warning(
                    "Bad output data structure in '{}'".format(handler_def.uri)
                )
                # TODO: warn about bad output
                pass
        else:
            # TODO: warn
            pass

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
    URI_REGEX = re.compile(r'\{([^\/\?\}]*)\}')

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
        self.query_args = []

        self.consumes = getattr(handler, 'consumes', None)
        self.produces = getattr(handler, 'produces', None)
        self.errors = getattr(handler, 'errors', [])
        self.deprecated = getattr(handler, 'deprecated', False)

        self._extract_arguments()
        self.operation_definition = self._generate_operation_definition()

    def _extract_path_args(self):
        """Extracts path arguments from the URI."""
        regex = re.compile(self.uri_regex)
        path_arg_names = list(regex.groupindex.keys())

        for arg_name in path_arg_names:
            if arg_name in self._params:
                if self._params[arg_name].default is not Parameter.empty:
                    raise DefinitionError(
                        "Path argument '{}' must not be optional in '{}'"
                        .format(
                            arg_name,
                            self.handler.__name__
                        )
                    )

                self.path_args.append(
                    PathParam(arg_name,
                              self._params[arg_name].annotation)
                )
            else:
                raise DefinitionError(
                    "Path argument '{}' must be expected by '{}'".format(
                        arg_name,
                        self.handler.__name__
                    )
                )

    def _extract_query_arguments(self):
        """
        Extracts query arguments from handler signature

        Should be called after path arguments are extracted.
        """
        for _, param in self._params.items():
            if param.name not in [a.name for a in self.path_args]:
                self.query_args.append(
                    QueryParam(param.name,
                               param.annotation,
                               param.default)
                )

    def _extract_arguments(self):
        """Extracts path and query arguments."""
        self._extract_path_args()
        self._extract_query_arguments()

    def _generate_operation_definition(self):
        summary, description = parse_docstring(self.handler.__doc__ or '')

        operation_id = '.'.join(
            [self.handler.__module__, self.handler.__name__]
        ).replace('.', '_')

        parameters = [q.generate_swagger() for q in self.path_args]
        parameters += [q.generate_swagger() for q in self.query_args]

        if self.consumes:
            parameters.append({
                'in': 'body',
                'name': 'body',
                'schema': self.consumes.json_schema
            })

        responses = {}
        if self.produces:
            responses['200'] = {
                'description': '',  # TODO: decide what to put down here
                'schema': self.produces.json_schema
            }
        else:
            responses['204'] = {
                'description': 'This endpoint does not return data.'
            }

        for error in self.errors:
            responses[str(error.code)] = {
                '$ref': '#/responses/{}'.format(error.__name__)
            }

        opdef = {
            'summary': summary,
            'description': description,
            'operationId': operation_id,
            'parameters': parameters,
            'responses': responses
        }

        if self.deprecated:
            opdef['deprecated'] = True

        return opdef


class SwaggerHandler(DefaultHandler):
    """
    The handler for Swagger.io (OpenAPI).

    This handler defined the GET method to output the Swagger.io (OpenAPI)
    definition for the Calm Application.
    """
    async def get(self):
        self._write_response(self._app.swagger_json)
