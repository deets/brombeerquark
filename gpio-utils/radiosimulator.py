from __future__ import print_function
from functools import partial
import time
import threading
import Queue

from tfa import TimedFiniteAutomaton

def simulate_gpio_events(queue):
    time.sleep(1.0)
    # just increase volume by pressing/releasing once
    queue.put("volume+pressed")
    queue.put("volume+released")
    time.sleep(3.0)
    # now just hold volume+pressed til 11!
    queue.put("volume+pressed")
    time.sleep(7.0)
    queue.put("volume+released")

    # now just hold volume-pressed til we are back to 1
    queue.put("volume-pressed")
    time.sleep(7.0)
    queue.put("volume-released")

    # finally, toggle play/pause
    queue.put("volume-pressed")
    time.sleep(0.1)
    queue.put("volume+pressed")
    # let go of both buttons
    queue.put("volume-release")
    queue.put("volume+released")


class Radio(object):
    MINVOL, MAXVOL = 1, 11
    SAME_TIME_THRESHOLD = .3

    def __init__(self):
        self._volume = self.MINVOL
        self.playing = True

        automat = TimedFiniteAutomaton("idle")
        automat.add_state("volume_up")
        automat.add_state("volume_down")
        automat.add_state("nudge_up")
        automat.add_state("nudge_down")
        automat.add_state("volume_up_or_toggle")
        automat.add_state("volume_down_or_toggle")
        automat.add_state("toggle_play_pause")

        # waiting for either volume change or toggling play/pause
        automat.add_transition("idle", "volume_up_or_toggle", "volume+pressed")
        automat.add_transition("idle", "volume_down_or_toggle", "volume-pressed")
        # after self.SAME_TIME_THRESHOLD seconds, we will transition to volue up/down
        # we will re-enter the state on .5 timer events to further increase volume
        automat.add_transition("volume_up_or_toggle", "volume_up", self.SAME_TIME_THRESHOLD)
        automat.add_transition("volume_down_or_toggle", "volume_down", self.SAME_TIME_THRESHOLD)
        automat.add_transition("volume_up", "volume_up", .5)
        automat.add_transition("volume_down", "volume_down", .5)
        automat.add_transition("volume_up", "idle", "volume+released")
        automat.add_transition("volume_down", "idle", "volume-released")
        # when we wait for toggle_play_pause, but already release,
        # just nudge the volume once in the respective direction!
        automat.add_transition("volume_up_or_toggle", "nudge_up", "volume+released")
        automat.add_transition("nudge_up", "idle")
        automat.add_transition("volume_down_or_toggle", "nudge_down", "volume-released")
        automat.add_transition("nudge_down", "idle")
        # if within this timeframe the opposite key was pressed, toggle!
        automat.add_transition("volume_up_or_toggle", "toggle_play_pause", "volume-pressed")
        automat.add_transition("volume_down_or_toggle", "toggle_play_pause", "volume+pressed")
        # from play_pause, transition automatically back to idle
        automat.add_transition("toggle_play_pause", "idle")

        self._automat = automat
        self._automat.add_state_change_listener(self._react_to_state_changes)

        print(automat.dot())


    def _react_to_state_changes(self, _from, to, _on):
        if to in ("volume_up", "nudge_up"):
            self.volume += 1
        elif to in ("volume_down", "nudge_down"):
            self.volume -= 1
        elif to == "toggle_play_pause":
            self.playing = not self.playing


    @property
    def volume(self):
        return self._volume


    @volume.setter
    def volume(self, value):
        self._volume = min(max(value, self.MINVOL), self.MAXVOL)


    def run(self):
        q = Queue.Queue()
        t = threading.Thread(target=partial(simulate_gpio_events, q))
        t.daemon = True
        t.start()
        self._automat.add_state_change_listener(self._print_status)
        while True:
            try:
                event = q.get(block=True, timeout=.1)
            except Queue.Empty: #timeout
                self._automat.tick()
            else:
                print("feed", event)
                self._automat.feed(event)


    def _print_status(self, *_a):
        print("Playing: {}, Volume: {}, State: {} ".format(
            self.playing,
            self.volume,
            self._automat.state,
            )
        )


def main():
    radio = Radio()
    radio.run()

if __name__ == '__main__':
    main()
