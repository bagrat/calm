from calm.testing import CalmHTTPTestCase

from calm import Application
from calm.decorator import produces, consumes


app = Application()


@app.get('/regular_order')
@produces(int)
@consumes(str)
def regular_order_handler(request):
    pass


@consumes(str)
@produces(int)
@app.get('/regular_order')
def reverse_order_handler(request):
    pass


class SpecTests(CalmHTTPTestCase):
    def get_calm_app(self):
        global app
        return app

    def test_produces_consumes(self):
        handler = regular_order_handler
        self.assertIsNotNone(handler.handler_def)
        self.assertEqual(handler.handler_def.consumes, str)
        self.assertEqual(handler.handler_def.produces, int)

        handler = reverse_order_handler
        self.assertIsNotNone(handler.handler_def)
        self.assertEqual(handler.handler_def.consumes, str)
        self.assertEqual(handler.handler_def.produces, int)
