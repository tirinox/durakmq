from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.label import Label


class GameMessageLabel(Label):
    def fade_in(self, *_):
        anim = Animation(opacity=1.0, duration=0.5)
        anim.start(self)

    def fade_out(self, *_):
        anim = Animation(opacity=0, duration=0.5)
        anim.start(self)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_message(self, new_message, fade_after=-1):
        print(f'Message: {new_message!r}')
        if not new_message:
            self.fade_out()
        else:
            self.text = new_message
            self.fade_in()

            if fade_after >= 0:
                Clock.schedule_once(self.fade_out, fade_after)
