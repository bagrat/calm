from calm.testing import CalmHTTPTestCase

from calm import Application
from calm.decorator import produces, consumes
from calm.resource import Resource
from calm.ex import DefinitionError


app = Application('testapp', '1')


class ProdResource(Resource):
    pass


class ConsResource(Resource):
    pass


@app.get('/regular_order')
@produces(ProdResource)
@consumes(ConsResource)
def regular_order_handler(request):
    pass


@consumes(ConsResource)
@produces(ProdResource)
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
        self.assertEqual(handler.handler_def.consumes, ConsResource)
        self.assertEqual(handler.handler_def.produces, ProdResource)

        handler = reverse_order_handler
        self.assertIsNotNone(handler.handler_def)
        self.assertEqual(handler.handler_def.consumes, ConsResource)
        self.assertEqual(handler.handler_def.produces, ProdResource)

        self.assertRaises(DefinitionError, produces, int)
        self.assertRaises(DefinitionError, consumes, str)
