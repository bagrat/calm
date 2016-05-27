

import json

from tornado.testing import AsyncHTTPTestCase

from calm.codec import CalmJSONDecoder, CalmJSONEncoder
from calm.core import CalmApp


class CalmTestCase(AsyncHTTPTestCase):
    def get_calm_app(self):
        pass  # pragma: no cover

    def get_app(self):
        calm_app = self.get_calm_app()

        if calm_app is None or not isinstance(calm_app, CalmApp):
            raise NotImplementedError(  # pragma: no cover
                "Please implement CalmTestCase.get_calm_app()"
            )

        return calm_app.make_app()

    def _request(self, url, *args,
                 expected_code=200, json_body=None,
                 **kwargs):
        expected_result = kwargs.pop('expected_result', None)
        if expected_result:
            expected_json_body = {
                self.get_calm_app().config['plain_result_key']: expected_result
            }
        else:
            expected_json_body = kwargs.pop('expected_json_body', None)

        expected_body = kwargs.pop('expected_body', None)

        query_params = kwargs.pop('query_params', {})
        query_string = '&'.join(
            '='.join(str(e) for e in arg) for arg in query_params.items()
        )
        if query_string:
            url = url + '?' + query_string

        if ((kwargs.get('body') or json_body) and
                kwargs['method'] not in ('POST', 'PUT')):
            raise Exception(  # pragma: no cover
                "Cannot send body with methods other than POST and PUT"
            )

        if not kwargs.get('body'):
            if kwargs['method'] in ('POST', 'PUT'):
                if json_body:
                    kwargs['body'] = json.dumps(json_body, cls=CalmJSONEncoder)
                else:
                    kwargs['body'] = '{}'

        resp = self.fetch(url, *args, **kwargs)

        actual_code = resp.code
        self.assertEqual(actual_code, expected_code)

        if expected_body:
            self.assertEqual(resp.body.decode('utf-8'), expected_body)  # pragma: no cover

        if expected_json_body:
            actual_json_body = json.loads(resp.body.decode('utf-8'),
                                          cls=CalmJSONDecoder)
            self.assertEqual(expected_json_body, actual_json_body)

        return resp

    def get(self, url, *args, **kwargs):
        kwargs.update(method='GET')
        return self._request(url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        kwargs.update(method='POST')
        return self._request(url, *args, **kwargs)

    def put(self, url, *args, **kwargs):
        kwargs.update(method='PUT')
        return self._request(url, *args, **kwargs)

    def delete(self, url, *args, **kwargs):
        kwargs.update(method='DELETE')
        return self._request(url, *args, **kwargs)
