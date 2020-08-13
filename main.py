from kivy.config import Config
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout

from gui.animation import AnimationSystem
from gui.card import Card
from gui.game_layout import GameLayout
from gui.gm_label import GameMessageLabel
from util import rand_id, rand_circle_pos, debug_start
from net_game import DurakNetGame

debug_start()

Config.set('graphics', 'width', '480')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', False)

from kivy.app import App
from kivy.core.window import Window
from kivy.properties import NumericProperty, ObjectProperty
from durak import *
from kivy.clock import Clock, mainthread
from discovery_protocol import DiscoveryProtocol

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

    def player_take_cards(self, is_me):
        hand = self.my_cards if is_me else self.opp_cards
        for i, (c1, c2) in enumerate(self.field):
            hand.append(c1)
            c1.open = is_me
            if c2:
                hand.append(c2)
                c2.opened = is_me
        self.field.clear()
        self.update_field_and_hand()

    def update_cards_in_hand(self, container, is_my):
        n = len(container)
        for i, c in enumerate(container):
            c.set_animated_targets(*self.layout.pos_of_hand(i, n, is_my))

    def update_field_and_hand(self):
        n = len(self.field)
        for i, (c1, c2) in enumerate(self.field):
            c1.set_animated_targets(*self.layout.pos_of_field_cell(i, n, beneath=True))
            if c2:
                c2.set_animated_targets(*self.layout.pos_of_field_cell(i, n, beneath=False))

        self.update_cards_in_hand(self.my_cards, is_my=True)
        self.update_cards_in_hand(self.opp_cards, is_my=False)

    def put_card_to_field(self, wcard: Card, on_card=None):
        if not wcard:
            return

        # убрать карту из списка карт (моих или чужих)
        container = self.my_cards if wcard.opened else self.opp_cards
        container.remove(wcard)

        # открыть карту
        wcard.opened = True

        if on_card is None:
            self.field.append((wcard, None))
        else:
            on_card = tuple(on_card)  # по JSON приходят list, а карты у нас tuple!
            def_index = [i for i, (c1, _) in enumerate(self.field) if c1.as_tuple == on_card][0]
            c1, c2 = self.field[def_index]
            assert c2 is None
            self.field[def_index] = (c1, wcard)
            wcard.bring_to_front()

        # обновить атрибуты всех карт на поле и в руках
        self.update_field_and_hand()

    def show_error(self, message):
        self.error_label.update_message(message, fade_after=3.0)

    def on_press_card(self, wcard: Card, *_):
        if self.locked_controls:
            self.show_error('Подождите!')
            return

        card = wcard.as_tuple
        is_my_card = wcard in self.my_cards

        if self.game.is_my_turn:
            if is_my_card:
                if not self.game.attack(card):
                    self.show_error('Вы не можете пока ходить этой картой!')
        else:
            if self.game.state.any_unbeaten_cards:
                if is_my_card:
                    variants = self.game.state.defend_variants(card)
                    if not variants:
                        self.show_error('Этой картой вы ничего не побьете!')
                    elif len(variants) == 1:
                        self.game.defend(card, variants[0])
                    else:
                        self.def_card = card
                elif wcard in self.field and self.def_card:
                    if not self.game.defend(self.def_card, wcard):
                        self.show_error('Вы не можете так побить!')
                    self.def_card = None
            else:
                self.show_error('Подождите, пока вас атакуют...')

        # if wcard in self.my_cards or wcard in self.opp_cards:
        #     self.put_card_to_field(wcard)
        # debug
        # if len(self.field) == 3 and self.field[-1][1] is not None:
        #     self.locked_contorls = True
        #     Clock.schedule_once(self.throw_away_field, 1.0)
        #     Clock.schedule_once(lambda *_: self.give_cards(True), 1.0)  # debug

    def on_finish_button(self, *_):
        if self.locked_controls:
            return
        r = self.game.finish_turn()
        if r == TurnFinishResult.EMPTY:
            self.show_error('Никто еще не ходил!')
        elif r == TurnFinishResult.TOOK_CARDS:
            self.show_error('Вы взяли карты!')
        elif r == TurnFinishResult.CANT_FORCE_TO_TAKE:
            self.show_error('Соперник должен отбиться или взять!')
        elif r == TurnFinishResult.NORMAL_TURN:
            self.show_error('Ход перешел!')
        self.display_whose_turn()

    def on_disconnect_button(self, *_):
        self.reset()
        self.disconnect_button.visible = False

    def make_card(self, card, attrs=(0, 0, 0), opened=True, **kwargs):
        wcard = Card.make(card, opened=opened)
        wcard.set_animated_targets(*attrs)
        wcard.on_press = lambda: self.on_press_card(wcard, **kwargs)
        self.root.add_widget(wcard)
        return wcard

    def update_deck(self):
        self.deck_card.counter = len(self.game.state.deck)
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

        self.trump_card = self.make_card(self.game.state.trump, self.layout.pos_of_trump())
        self.deck_card = self.make_card(('', ''), self.layout.pos_of_deck())
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

    def give_cards(self, card_array: list):
        took_last = len(self.game.state.deck) == 0

        def give_one_card(*_):
            # hands = (self.my_cards, self.opp_cards) if me_first else (self.opp_cards, self.my_cards)
            player_index, card = card_array.pop(0)
            give_trump = took_last and len(card_array) == 0
            for_me = self.game.is_me(player_index)
            hand = self.my_cards if for_me else self.opp_cards

            if give_trump:
                # последняя карта - открытый козырь
                hand.index(self.trump_card)
                hand.append(self.trump_card)
                self.trump_card = None
                self.update_field_and_hand()
            elif self.trump_card:
                wcard = self.make_card(card, opened=for_me)
                wcard.set_immeditate_attr(*self.layout.pos_of_deck())
                hand.append(wcard)
                self.update_field_and_hand()
                self.update_deck()

            # todo: вставлять карты в руку в нужное отсортированное место

            if not card_array:
                # кончились карты - прекратим давать и вернем управление
                Clock.unschedule(give_one_card)
                self.locked_controls = False

        Clock.schedule_interval(give_one_card, 0.3)

    def search_card_widget(self, card):
        card = tuple(card)
        for wcard in self.all_card_widgets:
            if wcard.as_tuple == card:
                return wcard

    @mainthread
    def on_game_state_update(self, *_):
        # синхорнизировать состояние игры и GUI
        if not self.game_init:
            self.game_init = True
            self.make_cards()

        if self.game.winner is not None:
            if self.game.winner == self.game.ME:
                self.game_label.update_message('Вы победили!')
            else:
                self.error_label.update_message('Вы проиграли!')
            self.reset()
        else:
            up = self.game.state.last_update
            print(f'update: {up}')
            action = up.get('action')
            if action == UpdateAction.ATTACK:
                card = up['card']
                wcard = self.search_card_widget(card)
                self.put_card_to_field(wcard)
            elif action == UpdateAction.DEFEND:
                att_card = up['attacking_card']
                def_card = up['defending_card']
                self.put_card_to_field(self.search_card_widget(def_card), att_card)
            elif action == UpdateAction.FINISH_TURN:
                if 'clear_field' in up:
                    self.throw_away_field()
                else:
                    me_took = self.game.is_me(up['take_cards']['player'])
                    self.player_take_cards(is_me)
                self.give_cards(up['from_deck'])

            self.toggle_button(self.finish_button, True, "Бито" if self.game.is_my_turn else "Взять карты!")

    def reset(self):
        if self.game:
            self.game.stop()  # остановить поток чтения и забыть игру
            self.game = None
        self.game_init = False
        self.locked_controls = True  # заблокировать клики по картам
        self.remove_all_cards_animated()  # убрать все карты с поля
        Clock.schedule_once(self.scan, 3.0) # начать новый поиск через некоторое время
        self.def_card = None
        self.toggle_button(self.disconnect_button, False)
        self.toggle_button(self.finish_button, False)

    @mainthread
    def on_opponent_quit(self):
        """ Если соперник покинул игру """
        self.show_error('Игрок вышел')
        self.reset()

    @mainthread
    def on_found_peer(self, addr, peer_id):
        print(f'Найден соперник {peer_id}@{addr}')
        self.discovery = None

        # соперник найден, создаем новую игру с ним по сети
        self.game = DurakNetGame(self.my_pid, peer_id, addr[0], [PORT_NO, PORT_NO_AUX])
        self.game.on_state_updated = self.on_game_state_update
        self.game.on_opponent_quit = self.on_opponent_quit
        self.game.start()

        self.locked_controls = False

        self.toggle_button(self.disconnect_button, True)
        self.toggle_button(self.finish_button, True)

        self.game_label.update_message('Соперник найден!', fade_after=2.0)
        self.display_whose_turn()

    def scan(self, *_):
        # начать сканирование, если еще не начато
        if not self.discovery:
            self.discovery = DiscoveryProtocol(self.my_pid, PORT_NO)
            self.discovery.run_in_background(self.on_found_peer)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.field = []
        self.my_cards = []
        self.opp_cards = []
        self.locked_controls = False
        self.my_pid = rand_id()
        self.def_card = None
        self.trump_card = None
        self.deck_card = None
        self.game: DurakNetGame = None
        self.game_init = False
        self.discovery = None

    def build(self):
        Builder.load_file('durak.kv')
        return MainLayout()

    def display_whose_turn(self):
        def _inner(*_):
            self.game_label.update_message('Ваш ход!' if self.game.is_my_turn else 'Ход соперника!')

        Clock.schedule_once(_inner, 3.0)

    def toggle_button(self, button, is_on, text=''):
        """ Убирает или показывает кнопку на экране, а также обновляет ее текст """
        if text:
            button.text = text
        button.disabled = not is_on
        button.opacity = 1.0 if is_on else 0.0

    def on_start(self):
        super().on_start()

        self.width, self.height = Window.size
        self.layout = GameLayout(self.width, self.height)

        self.game_label: GameMessageLabel = self.root.ids.game_label
        self.error_label: GameMessageLabel = self.root.ids.error_label
        self.finish_button: Button = self.root.ids.finish_turn_button
        self.disconnect_button: Button = self.root.ids.disconnect_button
        self.toggle_button(self.disconnect_button, False)
        self.toggle_button(self.finish_button, False)

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
