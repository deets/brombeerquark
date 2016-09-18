# -*- encoding: utf-8 -*-
from __future__ import print_function
import time
from collections import defaultdict


class TimedFiniteAutomaton(object):

    class TimedEvent(object):

        def __init__(self, value):
            self.value = value


        def __str__(self):
            return "{:.2}s".format(self.value)


        def __le__(self, other):
            if isinstance(other, self.__class__):
                other = other.value
            return self.value < other


        def __eq__(self, other):
            if isinstance(other, self.__class__):
                other = other.value
            return self.value == other


    def __init__(self, start_state):
        self._transitions = {}
        self.add_state(start_state)
        self._state = start_state
        self._tick = self._timestamp = time.time()
        self._start_state = start_state
        self._callbacks = []


    @property
    def state(self):
        return self._state


    @state.setter
    def state(self, state):
        self._state = state
        self._timestamp = time.time()


    def add_state(self, state):
        assert state not in self._transitions, state
        self._transitions[state] = defaultdict(dict)


    def add_transition(self, from_, to, on=None):
        assert from_ in self._transitions
        assert to in self._transitions
        assert on not in self._transitions[from_], (from_, to, on)
        self._transitions[from_][self.TimedEvent(on) if isinstance(on, (int, long, float)) else on] = to


    def add_state_change_listener(self, listener):
        self._callbacks.append(listener)


    def feed(self, event=None):
        if event in self._transitions[self.state]:
            old = self.state
            self.state = self._transitions[self.state][event]
            self._trigger_callbacks(old, self.state, event)


    def tick(self, elapsed=None):
        if elapsed is None:
            elapsed = time.time() - self._tick
        self._tick += elapsed
        delta = self._tick - self._timestamp
        candidates = sorted(
            (on, to)
            for on, to in self._transitions[self.state].iteritems()
            if isinstance(on, self.TimedEvent)
        )
        for on, to in candidates:
            if on <= delta:
                old = self.state
                self.state = to
                self._trigger_callbacks(old, to, on)


    def _trigger_callbacks(self, from_, to, on):
        for listener in self._callbacks:
            listener(from_, to, on)
        # trigger epsilon events
        self.feed()


    def dot(self):
        def escape_name(name):
            if name is None:
                return "ε"
            return '"{}"'.format(name)

        def format_node(name):
            attrlist = []
            if name == self._start_state:
                attrlist.append("shape = doublecircle")
            if name == self.state:
                attrlist.append("style=filled")
            attrlist = "[{}]".format(", ".join(attrlist)) if attrlist else ""
            return '{}{};'.format(escape_name(name), attrlist)

        nodes = "\n".join(format_node(name) for name in sorted(self._transitions.keys()))

        edges = []
        for name, transitions in self._transitions.iteritems():
            for event, dest in transitions.iteritems():
                edges.append('{} -> {}[ label = {} ];'.format(
                    escape_name(name),
                    escape_name(dest),
                    escape_name(event),
                    )
                )
        edges = "\n".join(edges)
        return """digraph {{
        {}
        {}
        }}""".format(nodes, edges)


def test():
    tfa = TimedFiniteAutomaton("idle")
    tfa.add_state("volume_up")
    tfa.add_state("volume_down")
    tfa.add_transition("idle", "volume_up", "volume+")
    tfa.add_transition("volume_up", "idle")
    tfa.add_transition("idle", "volume_down", "volume-")
    tfa.add_transition("volume_down", "idle")
    print(tfa.dot())

if __name__ == '__main__':
    test()
