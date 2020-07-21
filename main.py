from kivy.config import Config

from gui.animation import AnimationSystem
from gui.card import Card
from gui.game_layout import GameLayout

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
    # fixme: возможно эти свойства уже доступны через API Kivy?
    width = NumericProperty()
    height = NumericProperty()

    texture = ObjectProperty()

    def throw_away_field(self, *_):
        for c1, c2 in self.field:
            self.layout.throw_away_card(c1)
            self.layout.throw_away_card(c2)
        self.field.clear()

    def on_press_card(self, wcard: Card, **kwargs):
        wcard.opened = True
        wcard.update_text()
        if not self.field:
            self.field = [(wcard, None)]
        else:
            last_c1, last_c2 = self.field[-1]
            if last_c2 is None:
                self.field[-1] = [last_c1, wcard]
                wcard.bring_to_front()
            else:
                self.field.append([wcard, None])

        n = len(self.field)
        for i, (c1, c2) in enumerate(self.field):
            c1.set_animated_targets(*self.layout.attr_to_field(i, n, beneath=True))
            if c2:
                c2.set_animated_targets(*self.layout.attr_to_field(i, n, beneath=False))

        # debug
        if len(self.field) == 3 and self.field[-1][1] is not None:
            Clock.schedule_once(self.throw_away_field, 1.0)

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
            self.make_card(card, self.layout.attr_to_my_hand(i, len(my_cards)))

        for i, card in enumerate(opp_cards, start=1):
            self.make_card(card, self.layout.attr_to_opp_hand(i, len(opp_cards)), opened=False)

        self.make_card(deck.pop(), self.layout.attr_to_trump())
        self.make_card((str(len(deck)), ''), self.layout.attr_to_deck())

    def on_start(self):
        super().on_start()

        self.width, self.height = Window.size
        self.layout = GameLayout(self.width, self.height)

        self.texture = Image(source='assets/bg.jpg').texture
        self.texture.wrap = 'repeat'
        self.texture.uvsize = (1, 1)

        self.make_cards()

        self.field = []

        self.animator = AnimationSystem(self.root)
        self.animator.run()


if __name__ == '__main__':
    DurakFloatApp().run()
