from unittest.mock import MagicMock
from tornado.testing import AsyncHTTPTestCase

from calm import Application


app = Application()


@app.get('/async/:param')
async def async_mock(request, param):
    return param


@app.post('/sync/:param')
def sync_mock(request, param):
    return param


@app.get('/part1/', '/part2')
async def fragments_handler(request, retparam):
    return retparam


class CoreTests(AsyncHTTPTestCase):
    def get_app(self):
        global app
        return app.make_app()

    def test_sync_async(self):
        async_expected = 'async_result'
        sync_expected = 'sync_result'

        response = self.fetch('/async/{}'.format(async_expected))
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body.decode('utf-8'), async_expected)

        response = self.fetch('/sync/{}'.format(sync_expected), method="POST",
                              body="{}")
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body.decode('utf-8'), sync_expected)

    def test_uri_fragments(self):
        expected = 'expected_result'

        response = self.fetch('/part1/part2/?retparam={}'.format(expected))
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body.decode('utf-8'), expected)
