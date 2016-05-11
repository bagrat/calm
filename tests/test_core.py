from unittest.mock import MagicMock
from tornado.testing import AsyncHTTPTestCase

from tests import CalmTestCase
from calm import Application
from calm.ex import CoreError


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


@app.put('/default')
async def default_handler(request, p1, p2, p3, p4,
                          p5, p6, p7, p8='p8', p9='p9'):
    return p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9


@app.get('/required_query_param')
def required_query_param(request, query_param):
    pass


class CoreTests(CalmTestCase):
    def get_app(self):
        global app
        return app.make_app()

    def test_sync_async(self):
        async_expected = 'async_result'
        sync_expected = 'sync_result'

        response = self.get('/async/{}'.format(async_expected))
        self.assertEqual(response.body.decode('utf-8'), async_expected)

        response = self.post('/sync/{}'.format(sync_expected))
        self.assertEqual(response.body.decode('utf-8'), sync_expected)

    def test_uri_fragments(self):
        expected = 'expected_result'

        response = self.get('/part1/part2/?retparam={}'.format(expected))
        self.assertEqual(response.body.decode('utf-8'), expected)

    def test_default(self):
        p_values = {
            'p' + str(i): 'p' + str(i)
            for i in range(1, 8)
        }

        response = self.put('/default?{}'.format(
            '&'.join(['='.join(kv) for kv in p_values.items()])
        ))
        self.assertEqual(
            response.body.decode('utf-8'),
            ''.join(
                sorted(
                    [v for v in p_values.values()] + ['p8', 'p9']
                )
            )
        )

        p_values = {
            'p' + str(i): 'p' + str(i)
            for i in range(1, 9)
        }

        response = self.put('/default?{}'.format(
            '&'.join(['='.join(kv) for kv in p_values.items()])
        ))
        self.assertEqual(
            response.body.decode('utf-8'),
            ''.join(
                sorted(
                    [v for v in p_values.values()] + ['p9']
                )
            )
        )

    def test_definition_errors(self):
        async def missing_path_param(request):
            pass

        self.assertRaises(CoreError,
                          app.delete('/missing_path_param/:param'),
                          missing_path_param)

        async def default_path_param(request, param='default'):
            pass

        self.assertRaises(CoreError,
                          app.delete('/default_path_param/:param'),
                          default_path_param)

    def test_required_query_param(self):
        self.get('/required_query_param',
                 expected_code=400)

    def test_method_not_allowed(self):
        self.post('/async/something',
                  expected_code=405)
