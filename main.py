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

    def attr_to_trump(self):
        return self.width * 0.83, self.height / 2, 90

    def attr_to_deck(self):
        return self.width * 0.93, self.height / 2, 0

    def attr_to_field(self, i, n, beneath):
        x_step = self.width * 0.15
        x_start = self.width * 0.12
        width = x_start + x_step * n
        if width >= self.width * 0.8:
            x_step = (self.width * 0.8 - x_start) / (n + 1)
        ang = -10.0 if beneath else 10.0
        x = x_start + i * x_step
        y = self.height * 0.5 + (-0.04 if beneath else 0.04) * self.height
        return x, y, ang

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

    def bring_to_front(self, w: Card):
        parent = w.parent
        parent.remove_widget(w)
        parent.add_widget(w)

    def on_press_card(self, wcard: Card, **kwargs):
        wcard.opened = True
        wcard.update_text()
        if not self.field:
            self.field = [(wcard, None)]
        else:
            last_c1, last_c2 = self.field[-1]
            if last_c2 is None:
                self.field[-1] = [last_c1, wcard]
                self.bring_to_front(wcard)
            else:
                self.field.append([wcard, None])

        n = len(self.field)
        for i, (c1, c2) in enumerate(self.field):
            c1.set_animated_targets(*self.attr_to_field(i, n, beneath=True))
            if c2:
                c2.set_animated_targets(*self.attr_to_field(i, n, beneath=False))

    def make_card(self, card, attrs, opened=True, **kwargs):
        wcard = Card.make(card, opened=opened)
        wcard.set_animated_targets(*attrs)
        wcard.on_press = lambda: self.on_press_card(wcard, **kwargs)
        self.root.add_widget(wcard)

    def make_cards(self):
        deck = list(DECK)
        random.shuffle(deck)
        my_cards = [deck.pop() for _ in range(CARDS_IN_HAND_MAX)]
        opp_cards = [deck.pop() for _ in range(CARDS_IN_HAND_MAX)]

        for i, card in enumerate(my_cards, start=1):
            self.make_card(card, self.attr_to_my_hand(i, len(my_cards)))

        for i, card in enumerate(opp_cards, start=1):
            self.make_card(card, self.attr_to_opp_hand(i, len(opp_cards)), opened=False)

        self.make_card(deck.pop(), self.attr_to_trump())
        self.make_card((str(len(deck)), ''), self.attr_to_deck())

    def on_start(self):
        super().on_start()

        self.width, self.height = Window.size

        self.texture = Image(source='assets/bg.jpg').texture
        self.texture.wrap = 'repeat'
        self.texture.uvsize = (1, 1)

        self.make_cards()

        self.field = []

        Clock.schedule_interval(self.update, 1.0 / 60.0)


if __name__ == '__main__':
    DurakFloatApp().run()
