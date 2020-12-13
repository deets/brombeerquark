import os
from functools import partial
import logging
import json

import tornado.ioloop
import tornado.web
import tornado.websocket

import gpiozero

from tornado.options import define, options, parse_command_line

define("port", default=12345, help="run on the given port", type=int)


# I suggest using better names here, such as
# bathroom_light or trapdoor_release
BUTTON_DEFINITIONS = {
    "number20": 20,
    "number16": 16,
    "number21": 21,
}

BOUNCE_TIME = .01


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    CLIENTS = {}

    def open(self, *args):
        self.id = self.get_argument("id")
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
            client["write_message"](json.dumps(value))


def button_callback(ioloop, name, button):
    ioloop.add_callback(
        partial(
            WebSocketHandler.dispatch,
            {name: button.value}
        )
    )


def setup_buttons(ioloop):
    res = []
    for name, pin in BUTTON_DEFINITIONS.items():
        button = gpiozero.Button(pin, bounce_time=BOUNCE_TIME)
        button.when_pressed = partial(button_callback, ioloop, name)
        button.when_released = partial(button_callback, ioloop, name)
        res.append(button)
    return res


def main():
    parse_command_line()

    logging.basicConfig(
        level=logging.INFO,
    )

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
    app.listen(options.port)
    ioloop = tornado.ioloop.IOLoop.instance()

    buttons = setup_buttons(ioloop)
    ioloop.start()


if __name__ == '__main__':
    main()
