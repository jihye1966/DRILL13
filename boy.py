from pathlib import Path

from pico2d import (
    SDL_KEYDOWN,
    SDL_KEYUP,
    SDLK_LEFT,
    SDLK_RIGHT,
    SDLK_a,
    SDLK_d,
    SDLK_SPACE,
    get_time,
    load_image,
)
from transitions import Machine


class AutoRun:
    SPEED = 780
    SCALE = 1.5
    DURATION = 5.0
    LEFT_LIMIT = 75
    RIGHT_LIMIT = 725

    def update(self, boy, elapsed):
        boy.auto_run_time += elapsed
        boy.x += self.SPEED * elapsed * boy.face_dir
        if boy.x >= self.RIGHT_LIMIT:
            boy.x = self.RIGHT_LIMIT
            boy.face_dir = -1
        elif boy.x <= self.LEFT_LIMIT:
            boy.x = self.LEFT_LIMIT
            boy.face_dir = 1


class Boy:
    IDLE = 'IDLE'
    RUN = 'RUN'
    SLEEP = 'SLEEP'
    AUTO_RUN = 'AUTO_RUN'
    IDLE_TIMEOUT = 5.0

    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.speed = 500
        self.left_pressed = False
        self.right_pressed = False
        self.idle_time = 0.0
        self.auto_run_time = 0.0
        self.auto_run = AutoRun()
        self.last_update_time = get_time()
        asset_path = Path(__file__).resolve().parent / 'animation_sheet.png'
        self.image = load_image(str(asset_path))
        self.machine = Machine(
            model=self,
            states=[self.IDLE, self.RUN, self.SLEEP, self.AUTO_RUN],
            initial=self.IDLE,
            auto_transitions=False
        )
        self.machine.add_transition('start_running', self.IDLE, self.RUN)
        self.machine.add_transition('stop_running', self.RUN, self.IDLE)
        self.machine.add_transition('fall_asleep', self.IDLE, self.SLEEP)
        self.machine.add_transition('wake_up', self.SLEEP, self.IDLE)
        self.machine.add_transition('wake_and_run', self.SLEEP, self.RUN)
        self.machine.add_transition('start_auto_run', self.IDLE, self.AUTO_RUN)
        self.machine.add_transition('stop_auto_run', self.AUTO_RUN, self.IDLE)
        self.machine.add_transition('cancel_auto_run', self.AUTO_RUN, self.RUN)

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_SPACE and self.state == self.SLEEP:
                self.wake_up()
                self.idle_time = 0.0
                return

            if event.key == SDLK_a and self.state == self.IDLE:
                self.start_auto_run()
                self.auto_run_time = 0.0
                return

            if event.key in (SDLK_LEFT, SDLK_a):
                self._press_direction(-1)
            elif event.key in (SDLK_RIGHT, SDLK_d):
                self._press_direction(1)
        elif event.type == SDL_KEYUP:
            if event.key in (SDLK_LEFT, SDLK_a):
                self.left_pressed = False
            elif event.key in (SDLK_RIGHT, SDLK_d):
                self.right_pressed = False

        moving = self.left_pressed or self.right_pressed
        if moving and self.state == self.IDLE:
            self.start_running()
        elif not moving and self.state == self.RUN:
            self.stop_running()

    def _press_direction(self, direction):
        if self.state == self.AUTO_RUN:
            self.cancel_auto_run()
            self.auto_run_time = 0.0
        elif self.state == self.SLEEP:
            self.wake_and_run()
            self.idle_time = 0.0

        self.left_pressed = direction < 0
        self.right_pressed = direction > 0
        self.face_dir = direction

    def update(self):
        now = get_time()
        elapsed = now - self.last_update_time
        self.last_update_time = now

        if self.state == self.IDLE:
            self.idle_time += elapsed
            if self.idle_time >= self.IDLE_TIMEOUT:
                self.fall_asleep()
        elif self.state == self.AUTO_RUN:
            self.auto_run.update(self, elapsed)
            if self.auto_run_time >= AutoRun.DURATION:
                self.stop_auto_run()
        else:
            self.idle_time = 0.0

        self.frame = (self.frame + 1) % 8
        if self.state == self.RUN:
            if self.left_pressed:
                self.x -= self.speed * elapsed
            if self.right_pressed:
                self.x += self.speed * elapsed
            self.x = max(50, min(750, self.x))

    def draw(self):
        if self.state == self.SLEEP:
            self.image.clip_composite_draw(
                0, 300, 100, 100, 1.5708, '', self.x, self.y - 30, 100, 100
            )
            return

        if self.state == self.AUTO_RUN:
            row = 100 if self.face_dir == 1 else 0
            size = int(100 * AutoRun.SCALE)
            self.image.clip_draw(
                self.frame * 100, row, 100, 100,
                self.x, self.y, size, size
            )
            return

        if self.state == self.RUN:
            row = 100 if self.face_dir == 1 else 0
        else:
            row = 300 if self.face_dir == 1 else 200
        self.image.clip_draw(self.frame * 100, row, 100, 100, self.x, self.y)
