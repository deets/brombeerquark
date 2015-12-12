import os
import threading
import time
from functools import partial

import tornado.ioloop
import tornado.web
import tornado.websocket

from tornado.options import define, options, parse_command_line

define("port", default=12345, help="run on the given port", type=int)


class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render("index.html")


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    CLIENTS = {}

    def open(self, *args):
        self.id = self.get_argument("id")
        self.stream.set_nodelay(True)
        self.CLIENTS[self.id] = {
            "id": self.id,
            "object": self,
            "write_message": self.write_message,
        }


    def on_message(self, message):
        pass


    def on_close(self):
        if self.id in self.CLIENTS:
            del self.CLIENTS[self.id]


    @classmethod
    def dispatch(cls, value):
        for client in cls.CLIENTS.values():
            client["write_message"](repr(value))


def gpio_loop():
    ioloop = tornado.ioloop.IOLoop.current()
    value = True

    while True:
        time.sleep(1.0)
        value = not value
        ioloop.add_callback(partial(WebSocketHandler.dispatch, value))


def main():
    parse_command_line()

    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
    }

    app = tornado.web.Application(
        [
            (r'/', IndexHandler),
            (r'/ws', WebSocketHandler),
        ],
        **settings
    )
    t = threading.Thread(target=gpio_loop)
    t.setDaemon(True)
    t.start()
    app.listen(options.port)
    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()


if __name__ == '__main__':
    main()
