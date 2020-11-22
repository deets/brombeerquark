import os
import time
from functools import partial
import tkinter as tk
from gpiozero import Device, Button, LED
from collections import deque

INPUT_A = 10
INPUT_B = 11

# This is only for mocking things on a PC!
# The Bridge works without the following
# lines for a real gpiozero
from tkgpiozero import PinFactory
Device.pin_factory = PinFactory()
Device.pin_factory.toggle_periodic(INPUT_A, 1.0)
Device.pin_factory.toggle_periodic(INPUT_B, .3)


class TkGpioZeroBridge:

    def __init__(self, root):
        self._root = root
        read_fd, self._write_fd = os.pipe()
        root.createfilehandler(read_fd, tk.READABLE, self._event_callback)
        self._button_events = deque()

    def register_button(self, button, callback):
        button.when_pressed = partial(self._button_callback, callback)

    def _button_callback(self, callback):
        self._button_events.append(callback)
        # just signal the mainloop!
        os.write(self._write_fd, b"!")

    def _event_callback(self, fd, _mask):
        # we always know there is just one byte
        # in there, we just consume that away as
        # the purpose of this is to wake us up.
        os.read(fd, 100)
        try:
            while True:
                # invoke our callbacks
                self._button_events.pop()()
        except IndexError:
            pass


class Application:

    def __init__(self, root):
        label = tk.Label(master=root, text="Threadmagie hier drunter:")
        label.pack()
        self._messages_from_automaton = tk.Label(master=root, text="")
        self._messages_from_automaton.pack()
        self._start = time.monotonic()

    def set_text(self, text):
        self._messages_from_automaton["text"] = text


def main():
    root = tk.Tk()
    bridge = TkGpioZeroBridge(root)
    button_a = Button(INPUT_A)
    button_b = Button(INPUT_B)
    app = Application(root)
    bridge.register_button(button_a, partial(app.set_text, "Button A"))
    bridge.register_button(button_b, partial(app.set_text, "Button B"))
    root.mainloop()


if __name__ == '__main__':
    main()
