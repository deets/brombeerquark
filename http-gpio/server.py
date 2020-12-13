import os
from functools import partial
import logging
import json
import datetime

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

OUTPUT_DEFINITIONS = {
    "number26": (26, None),
    "number19": (19, datetime.timedelta(seconds=.1)),
}

BOUNCE_TIME = .01


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    CLIENTS = {}

    def initialize(self, output_pins):
        self._output_pins = output_pins

    def open(self, *args):
        self.id = self.get_argument("id")
        self.CLIENTS[self.id] = {
            "id": self.id,
            "object": self,
            "write_message": self.write_message,
        }

    def on_message(self, message):
        message = json.loads(message)
        for name, value in message.items():
            if name in self._output_pins:
                self._output_pins[name].value = value

    def on_close(self):
        if self.id in self.CLIENTS:
            del self.CLIENTS[self.id]

    @classmethod
    def dispatch(cls, value):
        for client in cls.CLIENTS.values():
            client["write_message"](json.dumps(value))


def button_callback(ioloop, button_state, name, value):
    button_state[name] = value
    ioloop.add_callback(
        partial(
            WebSocketHandler.dispatch,
            {name: value}
        )
    )


def setup_buttons(ioloop, button_state):
    res = {}
    for name, pin in BUTTON_DEFINITIONS.items():
        button = gpiozero.Button(pin, bounce_time=BOUNCE_TIME, pull_up=True)
        callback = partial(button_callback, ioloop, button_state, name)
        button.when_pressed = partial(callback, True)
        button.when_released = partial(callback, False)
        res[name] = button
    return res


def reset_button_state(ioloop, button_state, buttons):
    for name, button in buttons.items():
        value = button.value
        if name in button_state and button_state[name] != value:
            button_callback(ioloop, button_state, name, value)
    ioloop.add_timeout(
        datetime.timedelta(seconds=BOUNCE_TIME * 10),
        partial(reset_button_state, ioloop, button_state, buttons)
    )


class AutoTimetoutPin:

    def __init__(self, ioloop, pin, timeout):
        self._pin = gpiozero.LED(pin)
        self._ioloop = ioloop
        self._timeout = timeout

    @property
    def value(self):
        return self._pin.value

    @value.setter
    def value(self, value):
        self._pin.value = value
        self._ioloop.add_timeout(
            self._timeout,
            self._reset,
        )

    def _reset(self):
        self._pin.value = not self._pin.value


def setup_output_pins(ioloop):
    res = {}
    for name, spec in OUTPUT_DEFINITIONS.items():
        pin, timeout = spec
        if timeout is None:
            pin = gpiozero.LED(pin)
        else:
            pin = AutoTimetoutPin(ioloop, pin, timeout)
        res[name] = pin
    return res


def main():
    parse_command_line()

    logging.basicConfig(
        level=logging.INFO,
    )

    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
    }

    ioloop = tornado.ioloop.IOLoop.instance()

    output_pins = setup_output_pins(ioloop)
    app = tornado.web.Application(
        [
            (r'/', IndexHandler),
            (r'/ws', WebSocketHandler, dict(output_pins=output_pins)),
        ],
        **settings
    )
    app.listen(options.port)
    button_state = {}
    buttons = setup_buttons(ioloop, button_state)
    ioloop.add_timeout(
        datetime.timedelta(seconds=1),
        partial(reset_button_state, ioloop, button_state, buttons)
    )
    ioloop.start()


if __name__ == '__main__':
    main()
