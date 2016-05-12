import json
from tornado.testing import AsyncHTTPTestCase


class CalmTestCase(AsyncHTTPTestCase):
    def _request(self, *args, **kwargs):
        expected_status_code = kwargs.pop('expected_code', 200)
        expected_result = kwargs.pop('expected_result', None)
        if not expected_result:
            expected_json_body = kwargs.pop('expected_json_body', None)
        else:
            expected_json_body = {'result': expected_result}

        if expected_json_body:
            expected_json_body = json.dumps(expected_json_body)

        expected_body = kwargs.pop('expected_body', expected_json_body)

        resp = self.fetch(*args, **kwargs)

        actual_status_code = resp.code
        self.assertEqual(actual_status_code, expected_status_code)
        if expected_body:
            self.assertEqual(resp.body.decode('utf-8'), expected_body)

        return resp

    def get(self, *args, **kwargs):
        kwargs.update(method='GET')
        return self._request(*args, **kwargs)

    def post(self, *args, **kwargs):
        kwargs.update(method='POST')
        kwargs['body'] = kwargs.pop('body', None) or '{}'
        return self._request(*args, **kwargs)

    def put(self, *args, **kwargs):
        kwargs.update(method='PUT')
        kwargs['body'] = kwargs.pop('body', None) or '{}'
        return self._request(*args, **kwargs)

    def delete(self, *args, **kwargs):
        kwargs.update(method='DELETE')
        return self._request(*args, **kwargs)
