import json
import re
import inspect
import datetime
from collections import defaultdict

from tornado.web import Application, RequestHandler
from tornado.web import MissingArgumentError

from calm.ex import (DefinitionError, ServerError, ClientError,
                     BadRequestError, MethodNotAllowedError)
from calm.codec import CalmJSONEncoder, CalmJSONDecoder, ArgumentParser
from calm.service import CalmService


class CalmApp(object):
    URI_REGEX = re.compile(':([^\/\?:]*)')
    config = {
        'argument_parser': ArgumentParser,
        'plain_result_key': 'result',
        'error_key': 'error'
    }

    def __init__(self):
        super(CalmApp, self).__init__()

        self._app = None
        self._route_map = defaultdict(dict)

    def configure(self, **kwargs):
        self.config.update(kwargs)

    def make_app(self):
        route_defs = []

        for uri, methods in self._route_map.items():
            init_params = {
                **methods,
                'argument_parser': self.config.get('argument_parser',
                                                   ArgumentParser),
                'app': self
            }
            route_defs.append(
                (uri, MainHandler, init_params)
            )

        self._app = Application(route_defs)

        return self._app

    def _add_route(self, http_method, function, *uri, **kwargs):
        # Join the uri fragments
        uri = '/'.join(
            u.strip('/') for u in uri
        )
        uri = '/' + uri + '/?'

        # Convert colon-uri into a regex and then
        # get all the group names for further use
        path_params = self.URI_REGEX.findall(uri)
        for path_param in path_params:
            uri = uri.replace(
                ':{}'.format(path_param),
                '(?P<{}>[^\/\?]*)'.format(path_param)
            )
        regex = re.compile(uri)
        path_params = list(regex.groupindex.keys())

        # Get the arguments specification of the
        # decorated function to make appropriate
        # checks
        argspec = inspect.getfullargspec(function)
        all_args = argspec.args[1:]
        has_kwargs = argspec.varkw
        default_count = len(argspec.defaults or [])
        if default_count:
            required_args = all_args[-default_count]
            optional_args = all_args[-default_count:]
        else:
            required_args = all_args
            optional_args = []

        # Make sure no path param is defined as optional
        optional_path_params = set(
            path_params).intersection(optional_args)
        if optional_path_params:
            raise DefinitionError(
                "Path Parameters {} must not be optional in '{}'".format(
                    list(optional_args),
                    function.__name__
                )
            )

        if not has_kwargs and not set(path_params).issubset(required_args):
            missing_path_params = set(
                path_params).difference(required_args)
            raise DefinitionError(
                "Path Parameters {} must be expected by '{}'".format(
                    list(missing_path_params),
                    function.__name__
                )
            )

        all_query_params = list(
            set(all_args)
            .difference(path_params)
        )
        required_query_params = list(
            set(required_args)
            .intersection(all_query_params)
        )

        handler_def = {
            'function': function,
            'all_args': all_args,
            'path_params': path_params,
            'all_query_params': all_query_params,
            'required_query_params': required_query_params,
        }

        self._route_map[uri][http_method.lower()] = handler_def

    def _decorator(self, http_method, *uri, **kwargs):
        def wrapper(function):
            self._add_route(http_method, function, *uri, **kwargs)
            return function

        return wrapper

    def get(self, *uri, **kwargs):
        return self._decorator("GET", *uri, **kwargs)

    def post(self, *uri, **kwargs):
        return self._decorator("POST", *uri, **kwargs)

    def delete(self, *uri, **kwargs):
        return self._decorator("DELETE", *uri, **kwargs)

    def put(self, *uri, **kwargs):
        return self._decorator("PUT", *uri, **kwargs)

    def service(self, url):
        return CalmService(self, url)


class MainHandler(RequestHandler):
    BUILTIN_TYPES = (str, list, tuple, set, int, float, datetime.datetime)

    def __init__(self, *args, **kwargs):
        self._get_handler = kwargs.pop('get', None)
        self._post_handler = kwargs.pop('post', None)
        self._put_handler = kwargs.pop('put', None)
        self._delete_handler = kwargs.pop('delete', None)

        self._argument_parser = kwargs.pop('argument_parser')()
        self._app = kwargs.pop('app', None)

        super(MainHandler, self).__init__(*args, **kwargs)

    def _get_query_params(self, handler_def):
        query_params = {}
        for qp in handler_def['all_query_params']:
            try:
                query_params[qp] = self.get_query_argument(qp)
            except MissingArgumentError:
                if qp not in handler_def['required_query_params']:
                    continue

                raise BadRequestError(
                    "Missing required query param '{}'".format(qp)
                )

        return query_params

    def _cast_args(self, handler, args):
        arg_types = handler.__annotations__
        for arg in args:
            arg_type = arg_types.get(arg)

            if not arg_type:
                continue

            args[arg] = self._argument_parser.parse(arg_type, args[arg])

    def _parse_and_update_body(self, request):
        if request.body:
            try:
                json_body = json.loads(request.body.decode('utf-8'),
                                       cls=CalmJSONDecoder)
                request.body = json_body
            except json.JSONDecodeError:
                raise BadRequestError(
                    "Malformed request body. JSON is expected."
                )

    async def _handle_request(self, handler_def, **kwargs):
        if not handler_def:
            raise MethodNotAllowedError()

        handler = handler_def['function']
        kwargs.update(self._get_query_params(handler_def))
        self._cast_args(handler, kwargs)
        self._parse_and_update_body(self.request)
        if inspect.iscoroutinefunction(handler):
            resp = await handler(self.request, **kwargs)
        else:
            # TODO: warn about blocking call
            resp = handler(self.request, **kwargs)

        self._write_response(resp)

    async def get(self, **kwargs):
        await self._handle_request(self._get_handler, **kwargs)

    async def post(self, **kwargs):
        await self._handle_request(self._post_handler, **kwargs)

    async def put(self, **kwargs):
        await self._handle_request(self._put_handler, **kwargs)

    async def delete(self, **kwargs):
        await self._handle_request(self._delete_handler, **kwargs)

    def _write_response(self, response):
        if hasattr(response, '__json__'):
            result = response.__json__()
        elif isinstance(response, dict):
            result = response
        elif isinstance(response, self.BUILTIN_TYPES):
            result = {
                self._app.config['plain_result_key']: response
            }
        else:
            raise ServerError(
                "Could not serialize '{}' to JSON".format(
                    type(response).__name__
                )
            )

        self._write_dict(result)

    def _write_dict(self, response_dict):
        result = json.dumps(response_dict, cls=CalmJSONEncoder)

        self.write(result)

    def write_error(self, status_code, exc_info=None, **kwargs):
        if exc_info:
            exc_type, exc_inst, _ = exc_info
            if issubclass(exc_type, ClientError):
                self._write_client_error(exc_inst)
                return

        self._write_server_error()

    def _write_client_error(self, exc):
        result = {
            self._app.config['error_key']: exc.message or str(exc)
        }

        self.set_status(exc.code)
        self.write(json.dumps(result))

    def _write_server_error(self):
        result = {
            self._app.config['error_key']: 'Oops our bad.'
                                           'We are working to fix this!'
        }

        self.set_status(500)
        self.write(json.dumps(result))
