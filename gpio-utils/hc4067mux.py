# -*- coding: utf-8 -*-
# Copyright: 2020, deets. MIT licensed.
from gpiozero import DigitalOutputDevice

class HC4067Mux:

    def __init__(self, s0, s1, s2, s3):
        """
        Arguments s0 to s3 represent the address input as in the datasheet
        """
        self._outs = [DigitalOutputDevice(pin=pin) for pin in [s0, s1, s2, s3]]
        self.channel(0)

    def channel(self, value):
        """
        Select the muxed channel from 0 to 15
        """
        assert 0 <= value <= 15, "Can only mux 4 lines"
        for i, pin in enumerate(self._outs):
            pin.value = bool(1 << i & value)
