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

        self.give_cards(me_first=True)  # debug

    def update_cards_in_hand(self, container, is_my):
        n = len(container)
        for i, c in enumerate(container):
            c.set_animated_targets(*self.layout.attr_to_hand(i, n, is_my))

    def update_field_and_hand(self):
        n = len(self.field)
        for i, (c1, c2) in enumerate(self.field):
            c1.set_animated_targets(*self.layout.attr_to_field(i, n, beneath=True))
            if c2:
                c2.set_animated_targets(*self.layout.attr_to_field(i, n, beneath=False))

        self.update_cards_in_hand(self.my_cards, is_my=True)
        self.update_cards_in_hand(self.opp_cards, is_my=False)

    def put_card_to_field(self, wcard: Card):
        # убрать карту из списка карт (моих или чужих)
        container = self.my_cards if wcard.opened else self.opp_cards
        container.remove(wcard)

        # открыть карту
        wcard.opened = True

        if not self.field:
            # если это первая карта на поле
            self.field = [(wcard, None)]
        else:
            last_c1, last_c2 = self.field[-1]
            if last_c2 is None:
                # если не занято место сверху
                self.field[-1] = [last_c1, wcard]
                wcard.bring_to_front()
            else:
                # новая пара
                self.field.append([wcard, None])

        # обновить атрибуты всех карт на поле и в руках
        self.update_field_and_hand()

    def on_press_card(self, wcard: Card, **kwargs):
        if wcard in self.my_cards or wcard in self.opp_cards:
            self.put_card_to_field(wcard)

        # debug
        if len(self.field) == 3 and self.field[-1][1] is not None:
            Clock.schedule_once(self.throw_away_field, 1.0)

    def make_card(self, card, attrs=(0, 0, 0), opened=True, **kwargs):
        wcard = Card.make(card, opened=opened)
        wcard.set_animated_targets(*attrs)
        wcard.on_press = lambda: self.on_press_card(wcard, **kwargs)
        self.root.add_widget(wcard)
        return wcard

    def update_deck(self):
        self.deck_card.counter = len(self.deck)
        if self.deck_card.counter <= 0:
            # сдвинуть за экран, если кончились карт
            self.deck_card.set_animated_targets(1.5 * self.width, 0.5 * self.height, 0)

    def make_cards(self):
        deck = list(DECK)
        random.shuffle(deck)
        my_cards = [deck.pop() for _ in range(CARDS_IN_HAND_MAX)]
        opp_cards = [deck.pop() for _ in range(CARDS_IN_HAND_MAX)]

        self.deck = deck
        self.field = []
        self.my_cards = []
        self.opp_cards = []

        for i, card in enumerate(my_cards, start=1):
            wcard = self.make_card(card)
            self.my_cards.append(wcard)

        for i, card in enumerate(opp_cards, start=1):
            wcard = self.make_card(card, opened=False)
            self.opp_cards.append(wcard)

        self.update_field_and_hand()

        self.make_card(deck.pop(), self.layout.attr_to_trump())
        self.deck_card = self.make_card(('', ''), self.layout.attr_to_deck())
        self.update_deck()

    def give_cards(self, me_first):
        def give_one_card(*_):
            containers = (self.my_cards, self.opp_cards) if me_first else (self.opp_cards, self.my_cards)
            for container in containers:
                # todo: забрать последний козырь, если колодаа кончилась
                if len(container) < CARDS_IN_HAND_MAX and self.deck:
                    wcard = self.make_card(self.deck.pop(), opened=(container is self.my_cards))
                    self.layout.give_card(wcard, len(container) - 1, len(container))
                    container.append(wcard)
                    self.update_field_and_hand()
                    self.update_deck()
                    return # дали карту
            # если не получилось дать, то прекращаем давать
            Clock.unschedule(give_one_card)
        Clock.schedule_interval(give_one_card, 0.3)

    def on_start(self):
        super().on_start()

        self.width, self.height = Window.size
        self.layout = GameLayout(self.width, self.height)

        self.texture = Image(source='assets/bg.jpg').texture
        self.texture.wrap = 'repeat'
        self.texture.uvsize = (1, 1)

        self.make_cards()

        self.animator = AnimationSystem(self.root)
        self.animator.run()


if __name__ == '__main__':
    DurakFloatApp().run()
