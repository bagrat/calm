from tornado.testing import gen_test
from tornado.websocket import WebSocketHandler

from calm.testing import CalmWebSocketTestCase
from calm import Application
from calm.ex import DefinitionError


app = Application('testws', '1')


@app.websocket('/ws')
class SomeWebSocket(WebSocketHandler):
    OPEN_MESSAGE = "some open message"

    def open(self):
        self.write_message(self.OPEN_MESSAGE)

    def on_message(self, message):
        self.write_message(message)


class WebSocketTests(CalmWebSocketTestCase):
    def get_calm_app(self):
        global app
        return app

    def test_wrong_class(self):
        class WrongClass(object):
            pass

        self.assertRaises(DefinitionError, app.websocket('/wrong_class'),
                          WrongClass)
        self.assertRaises(DefinitionError, app.websocket('/wrong_class'),
                          1)

    @gen_test
    async def test_base_case(self):
        websocket = await self.init_websocket('/ws')

        msg = await websocket.read_message()
        self.assertEqual(msg, SomeWebSocket.OPEN_MESSAGE)

        some_msg = "some echo message"
        websocket.write_message(some_msg)
        msg = await websocket.read_message()
        self.assertEqual(msg, some_msg)

        websocket.close()
        msg = await websocket.read_message()
        self.assertEqual(msg, None)
