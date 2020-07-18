from kivy.config import Config

from gui.card import Card
from gui.utils import fast_dist
from math import sin, cos, pi

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

    def attr_to_my_hand(self, i, n):
        r = 0.9 * self.width
        cx, cy = (self.width * 0.5, -0.8 * r)
        min_ang, max_ang = -30, 30
        ang = min_ang + (max_ang - min_ang) / (n + 1) * i
        ang_r = ang / 180 * pi
        return cx + r * sin(ang_r), cy + r * cos(ang_r), -ang

    def attr_to_opp_hand(self, i, n):
        r = 0.9 * self.width
        cx, cy = (self.width * 0.5, self.height + 0.8 * r)
        min_ang, max_ang = -30, 30
        ang = min_ang + (max_ang - min_ang) / (n + 1) * i
        ang_r = ang / 180 * pi
        return cx + r * sin(ang_r), cy - r * cos(ang_r), ang

    @classmethod
    def set_animated_pos_attrs(cls, obj, attrs):
        x, y, r = attrs
        obj.target_position = x, y
        obj.target_rotation = r

    def update(self, dt):
        df = self.EXP_ATT * dt
        for child in self.root.children:
            if hasattr(child, 'target_position'):
                x, y = child.pos
                # компенсируем положение точки, смещая ее из нижнего левого угла в середину виджета
                x += child.size[0] / 2
                y += child.size[1] / 2
                tx, ty = child.target_position
                if fast_dist(x, y, tx, ty) >= 0.1:
                    x += (tx - x) * df
                    y += (ty - y) * df
                    # возвращаем обратно из середины точку к углу
                    child.pos = (x - child.size[0] / 2, y - child.size[1] / 2)
            if hasattr(child, 'target_rotation'):
                tr, r = child.target_rotation, child.rotation
                if abs(tr - r) >= 0.1:
                    child.rotation += (tr - r) * df

    def make_cards(self):
        deck = list(DECK)
        random.shuffle(deck)
        my_cards = [deck.pop() for _ in range(CARDS_IN_HAND_MAX)]
        opp_cards = [deck.pop() for _ in range(CARDS_IN_HAND_MAX)]

        for i, card in enumerate(my_cards, start=1):
            wcard = Card.make(card)
            self.set_animated_pos_attrs(wcard, self.attr_to_my_hand(i, len(my_cards)))
            self.root.add_widget(wcard)

        for i, card in enumerate(opp_cards, start=1):
            wcard = Card.make(card, opened=False)
            self.set_animated_pos_attrs(wcard, self.attr_to_opp_hand(i, len(opp_cards)))
            self.root.add_widget(wcard)

        wtrump = Card.make(deck.pop())
        wtrump.target_position = (self.width * 0.8, self.height / 2)
        wtrump.target_rotation = 90
        self.root.add_widget(wtrump)

        wdeck = Card.make(('27', ''))
        wdeck.target_position = (self.width * 0.9, self.height / 2)
        self.root.add_widget(wdeck)



    def on_start(self):
        super().on_start()

        self.width, self.height = Window.size

        self.texture = Image(source='assets/bg.jpg').texture
        self.texture.wrap = 'repeat'
        self.texture.uvsize = (1, 1)

        self.make_cards()

        Clock.schedule_interval(self.update, 1.0 / 60.0)


if __name__ == '__main__':
    DurakFloatApp().run()
