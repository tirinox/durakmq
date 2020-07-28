from kivy.config import Config
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout

from gui.animation import AnimationSystem
from gui.card import Card
from gui.game_layout import GameLayout
from gui.gm_label import GameMessageLabel
from util import rand_id, rand_circle_pos
from net_game import DurakNetGame

Config.set('graphics', 'width', '480')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', False)

from kivy.app import App
from kivy.core.window import Window
from kivy.properties import NumericProperty, ObjectProperty
from durak import *
from kivy.clock import Clock
import discovery_protocol

from itertools import zip_longest

PORT_NO = 37020
PORT_NO_AUX = 37021


class MainLayout(FloatLayout):
    ...


class DurakFloatApp(App):
    # fixme: возможно эти свойства уже доступны через API Kivy?
    width = NumericProperty()
    height = NumericProperty()

    texture = ObjectProperty()

    def throw_away_field(self, *_):
        for c in self.field_card_widgets:
            self.layout.throw_away_card(c)
        self.field.clear()

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
        if self.locked_controls:
            self.error_label.update_message('Подождите!', fade_after=2.0)
            return

        card = wcard.as_tuple
        is_my_card = wcard in self.my_cards

        if self.game.is_my_turn:
            if is_my_card:
                if not self.game.attack(card):
                    self.error_label.update_message('Вы не можете пока ходить этой картой!', fade_after=3.0)
        else:
            if is_my_card:
                variants = self.game.state.defend_variants(card)
                if not variants:
                    self.error_label.update_message('Этой картой вы ничего не побьете!', fade_after=3.0)
                elif len(variants) == 1:
                    self.game.defend(card, variants[0])
                else:
                    self.def_card = card
            elif wcard in self.field and self.def_card:
                if not self.game.defend(self.def_card, wcard):
                    self.error_label.update_message('Вы не можете так побить!', fade_after=3.0)
                self.def_card = None


        # if wcard in self.my_cards or wcard in self.opp_cards:
        #     self.put_card_to_field(wcard)
        # debug
        # if len(self.field) == 3 and self.field[-1][1] is not None:
        #     self.locked_contorls = True
        #     Clock.schedule_once(self.throw_away_field, 1.0)
        #     Clock.schedule_once(lambda *_: self.give_cards(True), 1.0)  # debug

    def on_finish_button(self, *_):
        ...

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
        for card in self.game.my_cards:
            wcard = self.make_card(card)
            self.my_cards.append(wcard)

        for card in self.game.opp_cards:
            wcard = self.make_card(card, opened=False)
            self.opp_cards.append(wcard)

        self.update_field_and_hand()

        self.trump_card = self.make_card(self.game.state.trump, self.layout.attr_to_trump())
        self.deck_card = self.make_card(('', ''), self.layout.attr_to_deck())
        self.update_deck()

    @property
    def field_card_widgets(self):
        return [c for pair in self.field for c in pair if c is not None]

    @property
    def all_card_widgets(self):
        return [*self.my_cards, *self.opp_cards, self.trump_card, self.deck_card, *self.field_card_widgets]

    def remove_all_cards_animated(self):
        for wcard in self.all_card_widgets:
            if wcard:
                wcard.set_animated_targets(*rand_circle_pos(), 0)
                wcard.destroy_card_after_delay(1.0)

        self.field.clear()
        self.my_cards = []
        self.opp_cards = []

    def give_cards(self, me_first):
        def give_one_card(*_):
            hands = (self.my_cards, self.opp_cards) if me_first else (self.opp_cards, self.my_cards)
            for hand in hands:
                hand_len = len(hand)
                if hand_len < CARDS_IN_HAND_MAX:
                    if self.deck:
                        wcard = self.make_card(self.deck.pop(), opened=(hand is self.my_cards))
                        wcard.set_immeditate_attr(*self.layout.attr_to_deck())
                        hand.append(wcard)
                        self.update_field_and_hand()
                        self.update_deck()
                        return  # дали карту
                    elif self.trump_card:
                        # последняя карта - открытый козырь
                        hand.append(self.trump_card)
                        self.trump_card = None
                        self.update_field_and_hand()
                        return  # дали карту

            # если не получилось дать, то прекращаем давать
            Clock.unschedule(give_one_card)
            self.locked_controls = False

        Clock.schedule_interval(give_one_card, 0.3)

    def on_game_state_update(self, state: Durak):
        # синхорнизировать состояние игры и GUI
        ...
        """
        1. карты в бито с поля
        2. дать карту из колоды в руку
        3. поместить карту из руки на поле а) атака б) побить
        """
        if self.game.winner is not None:
            if self.game.winner == self.game.ME:
                self.game_label.update_message('Вы победили!')
            else:
                self.error_label.update_message('Вы проиграли!')
            self.reset()

    def reset(self):
        self.game.stop()  # остановить поток чтения и забыть игру
        self.game = None
        self.game_init = False
        self.locked_controls = True  # заблокировать клики по картам
        self.remove_all_cards_animated()  # убрать все карты с поля
        Clock.schedule_once(self.scan, 3.0) # начать новый поиск через некоторое время
        self.def_card = None

    def on_opponent_quit(self):
        """ Если соперник покинул игру """

        # обновить надпись на экране
        self.error_label.update_message('Ваш соперник вышел!', fade_after=2.0)
        self.reset()

    def on_found_peer(self, addr, peer_id):
        # соперник найден, создаем новую игру с ним по сети
        self.game = DurakNetGame(self.my_pid, peer_id, addr, [PORT_NO, PORT_NO_AUX])
        self.game.on_state_updated = self.on_game_state_update
        self.game.on_opponent_quit = self.on_opponent_quit

        self.locked_controls = False

        self.game_label.update_message('Соперник найден!', fade_after=2.0)
        Clock.schedule_once(lambda *_: self.game_label.update_message('Ваш ход!'), 3.0)

    def scan(self, *_):
        discovery_protocol.DiscoveryProtocol(self.my_pid, PORT_NO).run_in_background(self.on_found_peer)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deck = []
        self.field = []
        self.my_cards = []
        self.opp_cards = []
        self.locked_controls = False
        self.my_pid = rand_id()
        self.def_card = None
        self.game_init = False

    def build(self):
        Builder.load_file('durak.kv')
        return MainLayout()

    def toggle_finish_button(self, is_on, text=''):
        """ Убирает или показывает кнопку на экране, а также обновляет ее текст """
        self.finish_button.text = text
        if is_on:
            self.finish_button.disabled = False
            self.finish_button.opacity = 1.0
        else:
            self.finish_button.disabled = True
            self.finish_button.opacity = 0.0

    def on_start(self):
        super().on_start()

        self.width, self.height = Window.size
        self.layout = GameLayout(self.width, self.height)

        self.game_label: GameMessageLabel = self.root.ids.game_label
        self.error_label: GameMessageLabel = self.root.ids.error_label
        self.finish_button: Button = self.root.ids.finish_turn_button
        self.toggle_finish_button(False)

        self.animator = AnimationSystem(self.root)
        self.animator.run()

        self.locked_controls = True

        self.game_label.update_message("Поиск соперника...")
        self.scan()

    def on_request_close(self, *args):
        self.game.stop()
        return True


if __name__ == '__main__':
    DurakFloatApp().run()
