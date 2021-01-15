# Copyright: 2021, Diez B. Roggisch, Berlin . All rights reserved.

import time
import queue
import random
# just for testing purposes
import threading


PULSES_PER_REVOLUTION = 20


class FakeGPIO:

    RISING = 1
    FALLING = 2

    def __init__(self, channel, period, variance=.1):
        self._channel = channel
        self._period = period
        self._variance = period * variance
        self._callback = lambda channel: None
        threading.Thread(target=self._run, daemon=True).start()

    def add_event_detect(self, channel, event, callback, bouncetime=0):
        assert self._channel == channel
        assert event == self.RISING
        self._callback = callback

    def _run(self):
        when = time.monotonic()
        while True:
            self._callback(self._channel)
            when += self._period + random.random() * 2 * self._variance - self._variance
            time.sleep(when - time.monotonic())


GPIO = FakeGPIO(20, 1 / PULSES_PER_REVOLUTION, variance=0.2)  # 1 RPM for 20 PPR, 20% variance


class RPMCounter:

    def __init__(self, channel, pulses_per_revolution, filter=0.1):
        self._pulses_per_revolution = pulses_per_revolution
        self._events = queue.Queue()
        self._filter = filter
        GPIO.add_event_detect(
            channel,
            GPIO.RISING,
            callback=self._rise_event,
            bouncetime=200
        )
        self._rpm = 0.0
        self._last_timestamp = None

    def _rise_event(self, _channel):
        self._events.put(time.monotonic())


    @property
    def rps(self):
        for _ in range(self._events.qsize()):
            ts = self._events.get()
            if self._last_timestamp is not None:
                diff = ts - self._last_timestamp
                residual = (1 / diff) / self._pulses_per_revolution - self._rpm
                self._rpm += self._filter * residual
            self._last_timestamp = ts
        return self._rpm

    @property
    def rpm(self):
        return self.rps * 60.0


def main():
    rpm_counter = RPMCounter(20, PULSES_PER_REVOLUTION)
    while True:
        print(rpm_counter.rpm)
        time.sleep(1)


if __name__ == '__main__':
    main()
