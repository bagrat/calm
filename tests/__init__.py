from tornado.testing import AsyncHTTPTestCase


class CalmTestCase(AsyncHTTPTestCase):
    def _request(self, *args, **kwargs):
        expected_status_code = kwargs.pop('expected_code', 200)

        resp = self.fetch(*args, **kwargs)

        actual_status_code = resp.code
        self.assertEqual(actual_status_code, expected_status_code)

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
