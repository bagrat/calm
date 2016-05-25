from calm.testing import CalmTestCase
from calm import Application
from calm.ex import DefinitionError, MethodNotAllowedError


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


@app.get('/blowup')
def blow_things_up(request):
    raise TypeError()


@app.delete('/response/:rtype')
def response_manipulations(request, rtype):
    if rtype == 'str':
        return 'test_result'
    elif rtype == 'list':
        return ['test', 'result']
    elif rtype == 'dict':
        return {'test': 'result'}
    elif rtype == 'object':
        class jsonable():
            def __json__(self):
                return {'test': 'result'}

        return jsonable()
    else:
        return object()


@app.get('/argtypes')
def argument_types(request, arg1, arg2: int):
    return arg1, arg2


class CoreTests(CalmTestCase):
    def get_app(self):
        global app
        return app.make_app()

    def test_sync_async(self):
        async_expected = 'async_result'
        sync_expected = 'sync_result'

        self.get('/async/{}'.format(async_expected),
                 expected_result=async_expected)

        self.post('/sync/{}'.format(sync_expected),
                  expected_result=sync_expected)

    def test_uri_fragments(self):
        expected = 'expected_result'

        self.get('/part1/part2/?retparam={}'.format(expected),
                 expected_result=expected)

    def test_default(self):
        p_values = {
            'p' + str(i): 'p' + str(i)
            for i in range(1, 8)
        }

        self.put('/default?{}'.format(
                '&'.join(['='.join(kv) for kv in p_values.items()])
            ),
            expected_result=''.join(
                    sorted(
                        [v for v in p_values.values()] + ['p8', 'p9']
                    )
            )
        )

        p_values = {
            'p' + str(i): 'p' + str(i)
            for i in range(1, 9)
        }

        self.put('/default?{}'.format(
                '&'.join(['='.join(kv) for kv in p_values.items()])
            ),
            expected_result=''.join(
                sorted(
                    [v for v in p_values.values()] + ['p9']
                )
            )
        )

    def test_definition_errors(self):
        async def missing_path_param(request):
            pass

        self.assertRaises(DefinitionError,
                          app.delete('/missing_path_param/:param'),
                          missing_path_param)

        async def default_path_param(request, param='default'):
            pass

        self.assertRaises(DefinitionError,
                          app.delete('/default_path_param/:param'),
                          default_path_param)

    def test_required_query_param(self):
        self.get('/required_query_param',
                 expected_code=400)

    def test_method_not_allowed(self):
        self.post('/async/something',
                  expected_code=405,
                  expected_json_body={
                      'error': MethodNotAllowedError.message
                  })

    def test_server_error(self):
        self.get('/blowup',
                 expected_code=500)

    def test_response_manipulations(self):
        self.delete('/response/str',
                    expected_result='test_result')

        self.delete('/response/list',
                    expected_result=["test", "result"])

        self.delete('/response/dict',
                    expected_json_body={"test": "result"})

        self.delete('/response/object',
                    expected_json_body={"test": "result"})

        self.delete('/response/error',
                    expected_code=500)

    def test_argument_types(self):
        args = {'arg1': 'something', 'arg2': 1234}
        expected = [args['arg1'], args['arg2']]

        self.get('/argtypes',
                 query_params=args,
                 expected_code=200,
                 expected_result=expected)
