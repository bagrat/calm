import json

from tornado.testing import AsyncHTTPTestCase

from calm.core import CalmApp


class CalmTestCase(AsyncHTTPTestCase):
    def get_calm_app(self):
        pass

    def get_app(self):
        calm_app = self.get_calm_app()

        if calm_app is None or not isinstance(calm_app, CalmApp):
            raise NotImplementedError(
                "Please implement CalmTestCase.get_calm_app()"
            )

        return calm_app.make_app()

    def _request(self, url, *args, **kwargs):
        expected_status_code = kwargs.pop('expected_code', 200)

        expected_result = kwargs.pop('expected_result', None)
        if expected_result:
            expected_json_body = {'result': expected_result}
        else:
            expected_json_body = kwargs.pop('expected_json_body', None)

        if expected_json_body:
            expected_json_body = json.dumps(expected_json_body)

        expected_body = kwargs.pop('expected_body', expected_json_body)

        query_params = kwargs.pop('query_params', {})
        query_string = '&'.join(
            '='.join(str(e) for e in arg) for arg in query_params.items()
        )
        if query_string:
            url = url + '?' + query_string

        resp = self.fetch(url, *args, **kwargs)

        actual_status_code = resp.code
        self.assertEqual(actual_status_code, expected_status_code)
        if expected_body:
            self.assertEqual(resp.body.decode('utf-8'), expected_body)

        return resp

    def get(self, url, *args, **kwargs):
        kwargs.update(method='GET')
        return self._request(url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        kwargs.update(method='POST')
        kwargs['body'] = kwargs.pop('body', None) or '{}'
        return self._request(url, *args, **kwargs)

    def put(self, url, *args, **kwargs):
        kwargs.update(method='PUT')
        kwargs['body'] = kwargs.pop('body', None) or '{}'
        return self._request(url, *args, **kwargs)

    def delete(self, url, *args, **kwargs):
        kwargs.update(method='DELETE')
        return self._request(url, *args, **kwargs)
