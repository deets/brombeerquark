import time
import unittest

from tfa import TimedFiniteAutomaton


class TFATests(unittest.TestCase):

    def test_start_state(self):
        a = TimedFiniteAutomaton("start")
        self.assertEqual("start", a.state)


    def test_adding_transition_and_walking_it(self):
        a = TimedFiniteAutomaton("start")
        a.add_state("end")
        a.add_transition("start", "end", "event")
        a.feed("event")
        self.assertEqual("end", a.state)


    def test_epsilon_transition_is_triggered_automatically(self):
        a = TimedFiniteAutomaton("start")
        a.add_state("end")
        a.add_transition("start", "end", "event")
        a.add_transition("end", "start")
        a.feed("event")
        self.assertEqual("start", a.state)


    def test_timed_transition(self):
        a = TimedFiniteAutomaton("start")
        a.add_state("end")
        a.add_transition("start", "end", 1.0)
        a.tick(2.0)
        self.assertEqual("end", a.state)


    def test_timed_transition_trigger_the_first_one(self):
        a = TimedFiniteAutomaton("start")
        a.add_state("a")
        a.add_state("b")
        a.add_transition("start", "a", 2.0)
        a.add_transition("start", "b", 1.0)
        a.tick(2.0)
        self.assertEqual("b", a.state)


    def test_timed_and_normal_transitions_mix(self):
        a = TimedFiniteAutomaton("start")
        a.add_state("a")
        a.add_state("b")
        a.add_transition("start", "a", "foo")
        a.add_transition("start", "b", 1.0)
        a.tick(2.0)
        self.assertEqual("b", a.state)


    def test_normal_and_timed_transitions_mix(self):
        a = TimedFiniteAutomaton("start")
        a.add_state("a")
        a.add_state("b")
        a.add_transition("start", "a", "foo")
        a.add_transition("start", "b", 1.0)
        a.feed("foo")
        self.assertEqual("a", a.state)


    def test_tick_without_arguments(self):
        a = TimedFiniteAutomaton("start")
        a.add_state("end")
        a.add_transition("start", "end", .2)
        a.tick()
        self.assertEqual("start", a.state)
        time.sleep(.3)
        a.tick()
        self.assertEqual("end", a.state)


    def test_callback_called_on_transition(self):
        a = TimedFiniteAutomaton("start")
        a.add_state("end")
        a.add_transition("start", "end", "event")
        transitions = []
        a.add_state_change_listener(lambda *a: transitions.append(a))
        a.feed("event")
        self.assertEqual(
            [("start", "end", "event")],
            transitions,
        )


    def test_callback_called_on_transition_to_self_on_event(self):
        a = TimedFiniteAutomaton("start")
        a.add_transition("start", "start", "event")
        transitions = []
        a.add_state_change_listener(lambda *a: transitions.append(a))
        a.feed("event")
        self.assertEqual(
            [("start", "start", "event")],
            transitions,
        )


    def test_callback_called_on_transition_to_self_on_timer(self):
        a = TimedFiniteAutomaton("start")
        a.add_transition("start", "start", 1.0)
        transitions = []
        a.add_state_change_listener(lambda *a: transitions.append(a))
        a.tick(2.0)
        self.assertEqual(
            [("start", "start", 1.0)],
            transitions,
        )
