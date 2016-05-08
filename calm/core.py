import re
import inspect
from collections import defaultdict
from itertools import repeat

from tornado.web import Application, RequestHandler
from tornado.web import MissingArgumentError

from calm.ex import (CoreError, ClientError, BadRequestError,
                     MethodNotAllowedError)


class CalmApp(object):
    URI_REGEX = re.compile(':([^\/\?:]*)')

    def __init__(self):
        super(CalmApp, self).__init__()

        self._app = None
        self._route_map = defaultdict(dict)

    def make_app(self):
        route_defs = []

        for uri, methods in self._route_map.items():
            route_defs.append(
                (uri, MainHandler, methods)
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
        argspec = inspect.getargspec(function)
        all_args = argspec.args[1:]
        has_kwargs = argspec.keywords
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
            raise CoreError(
                "Path Parameters {} must not be optional in '{}'".format(
                    list(optional_args),
                    function.__name__
                )
            )

        if not has_kwargs and not set(path_params).issubset(required_args):
            missing_path_params = set(
                path_params).difference(required_args)
            raise CoreError(
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


class MainHandler(RequestHandler):
    def __init__(self, *args, **kwargs):
        self._get_handler = kwargs.pop('get', None)
        self._post_handler = kwargs.pop('post', None)
        self._put_handler = kwargs.pop('put', None)
        self._delete_handler = kwargs.pop('delete', None)

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

    async def _handle_request(self, handler_def, **kwargs):
        if not handler_def:
            raise MethodNotAllowedError()

        handler = handler_def['function']
        try:
            kwargs.update(self._get_query_params(handler_def))
            if inspect.iscoroutinefunction(handler):
                resp = await handler(self.request, **kwargs)
            else:
                # TODO: warn about blocking call
                resp = handler(self.request, **kwargs)

            self.write(resp)
        except TypeError as ex:
            if 'argument' not in str(ex):
                # If the TypeError is obviously not because of
                # calling with wrong arguments, pass this up
                raise

            # TODO: list wrong arguments

    async def get(self, **kwargs):
        await self._handle_request(self._get_handler, **kwargs)

    async def post(self, **kwargs):
        await self._handle_request(self._post_handler, **kwargs)

    async def put(self, **kwargs):
        await self._handle_request(self._put_handler, **kwargs)

    async def delete(self, **kwargs):
        await self._handle_request(self._delete_handler, **kwargs)