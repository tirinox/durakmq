from kivy.config import Config

from gui.card import Card
from gui.utils import fast_dist

Config.set('graphics', 'width', '480')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', False)

from kivy.app import App
from kivy.core.window import Window
from kivy.properties import NumericProperty, ObjectProperty
from durak import *
from kivy.uix.image import Image
from kivy.clock import Clock
import random

PORT_NO = 37020
PORT_NO_AUX = 37021


class DurakFloatApp(App):
    EXP_ATT = 5.0

    # fixme: возможно эти свойства уже доступны через API Kivy?
    width = NumericProperty()
    height = NumericProperty()

    texture = ObjectProperty()

    def _attr_to_my_hand(self, i, n):
        ...

    def update(self, dt):
        df = self.EXP_ATT * dt
        for child in self.root.children:
            if hasattr(child, 'target_position'):
                x, y = child.pos
                tx, ty = child.target_position
                if fast_dist(x, y, tx, ty) >= 0.1:
                    x += (tx - x) * df
                    y += (ty - y) * df
                    child.pos = (x, y)
            if hasattr(child, 'target_rotation'):
                tr, r = child.target_rotation, child.rotation
                if abs(tr - r) >= 0.1:
                    child.rotation += (tr - r) * df

    def on_start(self):
        super().on_start()

        self.width, self.height = Window.size

        print(self.root.size)

        self.texture = Image(source='assets/bg.jpg').texture
        self.texture.wrap = 'repeat'
        self.texture.uvsize = (1, 1)

        card = Card.make((NOMINALS[2], CLUBS))
        self.root.add_widget(card)

        Clock.schedule_interval(self.update, 1.0 / 60.0)

        self.card = card  # debug
        Clock.schedule_interval(self.test_interval, 1.1)

    def test_interval(self, dt):
        self.card.target_position = (random.uniform(0, self.width), random.uniform(0, self.height))
        self.card.target_rotation = random.uniform(-45, 45)


if __name__ == '__main__':
    DurakFloatApp().run()
