import sys
import types
import unittest


clock = [0.0]


class FakeImage:
    def clip_draw(self, *args):
        pass

    def clip_composite_draw(self, *args):
        pass


def fake_get_time():
    return clock[0]


pico2d = types.ModuleType("pico2d")
pico2d.SDL_KEYDOWN = 1
pico2d.SDL_KEYUP = 2
pico2d.SDLK_LEFT = 10
pico2d.SDLK_RIGHT = 11
pico2d.SDLK_a = 12
pico2d.SDLK_d = 13
pico2d.SDLK_SPACE = 14
pico2d.get_time = fake_get_time
pico2d.load_image = lambda path: FakeImage()
sys.modules["pico2d"] = pico2d


class FakeEvent:
    def __init__(self, event_type, key):
        self.type = event_type
        self.key = key


class Machine:
    def __init__(self, model, states, initial, auto_transitions):
        model.state = initial
        self.model = model

    def add_transition(self, name, source, destination):
        def transition():
            if self.model.state != source:
                raise RuntimeError(f"invalid transition: {self.model.state} -> {destination}")
            self.model.state = destination

        setattr(self.model, name, transition)


transitions = types.ModuleType("transitions")
transitions.Machine = Machine
sys.modules["transitions"] = transitions

from boy import AutoRun, Boy


class BoyStateTests(unittest.TestCase):
    def setUp(self):
        clock[0] = 0.0
        self.boy = Boy()

    def advance(self, seconds):
        clock[0] += seconds
        self.boy.update()

    def test_direction_wakes_sleeping_boy_into_run(self):
        self.advance(Boy.IDLE_TIMEOUT)
        self.assertEqual(self.boy.state, Boy.SLEEP)

        self.boy.handle_event(FakeEvent(pico2d.SDL_KEYDOWN, pico2d.SDLK_RIGHT))

        self.assertEqual(self.boy.state, Boy.RUN)
        self.assertTrue(self.boy.right_pressed)

    def test_a_starts_keyless_auto_run(self):
        self.boy.handle_event(FakeEvent(pico2d.SDL_KEYDOWN, pico2d.SDLK_a))
        starting_x = self.boy.x
        self.advance(0.5)

        self.assertEqual(self.boy.state, Boy.AUTO_RUN)
        self.assertGreater(self.boy.x, starting_x)

    def test_auto_run_reverses_at_screen_edge(self):
        self.boy.handle_event(FakeEvent(pico2d.SDL_KEYDOWN, pico2d.SDLK_a))
        self.boy.x = AutoRun.RIGHT_LIMIT - 1
        self.advance(0.1)

        self.assertEqual(self.boy.x, AutoRun.RIGHT_LIMIT)
        self.assertEqual(self.boy.face_dir, -1)

    def test_direction_cancels_auto_run(self):
        self.boy.handle_event(FakeEvent(pico2d.SDL_KEYDOWN, pico2d.SDLK_a))
        self.boy.handle_event(FakeEvent(pico2d.SDL_KEYDOWN, pico2d.SDLK_LEFT))

        self.assertEqual(self.boy.state, Boy.RUN)
        self.assertEqual(self.boy.face_dir, -1)

    def test_auto_run_expires_after_five_seconds(self):
        self.boy.handle_event(FakeEvent(pico2d.SDL_KEYDOWN, pico2d.SDLK_a))
        self.advance(AutoRun.DURATION)

        self.assertEqual(self.boy.state, Boy.IDLE)


if __name__ == "__main__":
    unittest.main()
