from __future__ import print_function
import time
import argparse
import Queue
import RPi.GPIO as GPIO
import bisect

DESCRIPTION = """A simple tool to count events on a GPIO
PIN-Numbering is in BROADCOM!
"""

def main():
    parser = argparse.ArgumentParser(DESCRIPTION)
    parser.add_argument("--pin", type=int, required=True, help="The pin to use")
    parser.add_argument(
        "--event",
        choices=["RAISING", "FALLING", "BOTH"],
        default="FALLING",
        help="Which kind of event to count"
    )
    parser.add_argument(
        "--debounce",
        type=int,
        default=None,
        help="Debounce-time in ms, don't pass anything if you don't want to debounce"
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=None,
        help="If given, only count those pulses in the last SECONDS. Otherwise, count total"
    )

    opts = parser.parse_args()
    pin = opts.pin
    event_type = getattr(GPIO, opts.event)

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(pin, GPIO.IN)

    q = Queue.Queue()

    def callback(*args):
        q.put(time.time())

    if opts.debounce is not None:
        GPIO.add_event_detect(pin, event_type, callback, bouncetime=opts.debounce)
    else:
        GPIO.add_event_detect(pin, event_type, callback)

    pulses = []
    total = 0
    while True:
        # transfer pulses
        for _ in xrange(q.qsize()):
            pulses.append(q.get())
        if pulses:
            if opts.seconds is None:
                total += len(pulses)
                pulses = []
            else:
                then = pulses[-1] - opts.seconds
                pulses = pulses[bisect.bisect_left(pulses, then):]
                total = len(pulses)
            print(total)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
