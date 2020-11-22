# -*- coding: utf-8 -*-
# Copyright: 2020, Diez B. Roggisch, Berlin . All rights reserved.
import time
import sched
import threading
import gpiozero.pins


class Pin(gpiozero.pins.Pin):
    def __init__(self, factory, number):
        super().__init__()
        self._factory = factory
        self.number = number
        self._pull = "floating"
        self._edges = "none"
        self._when_changed = None
        self._state = 0

    def _get_state(self):
        return self._state

    def _set_state(self, value):
        if value == self._state:
            return
        edge = "rising" if value and not self._state else "falling"
        self._state = value
        if self._edges in ("both", edge) and self._when_changed is not None:
            self._when_changed(self._factory.ticks(), value)

    def _get_pull(self):
        return self._pull

    def _set_pull(self, value):
        self._pull = value

    def _get_edges(self):
        return self._edges

    def _set_edges(self, value):
        self._edges = value

    def _get_when_changed(self):
        return self._when_changed

    def _set_when_changed(self, value):
        self._when_changed = value


class PinFactory(gpiozero.pins.Factory):

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._pins = {}
        self._periodic_pins = []
        self._scheduler = None

    def pin(self, spec):
        if spec not in self._pins:
            self._pins[spec] = Pin(self, spec)
        return self._pins[spec]

    def ticks(self):
        return time.monotonic()

    def ticks_diff(self, later, earlier):
        return later - earlier

    def toggle_periodic(self, spec, timeout, bounces=0):
        if self._scheduler is None:
            self._scheduler = sched.scheduler()
            t = threading.Thread(target=self._drive_periodic_pins)
            t.daemon = True
            t.start()

        def toggle_callback():
            # it might not yet be registered
            if spec in self._pins:
                for _ in range(bounces):
                    self._pins[spec].state = not self._pins[spec].state
                    self._pins[spec].state = not self._pins[spec].state
                self._pins[spec].state = not self._pins[spec].state
            self._scheduler.enter(timeout, 0, toggle_callback)

        self._scheduler.enter(timeout, 0, toggle_callback)

    def _drive_periodic_pins(self):
        while True:
            self._scheduler.run()
            time.sleep(.1)
