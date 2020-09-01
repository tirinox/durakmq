from kivy.config import Config
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout

from util import rand_id, rand_circle_pos, debug_start

debug_start()

Config.set('graphics', 'width', '480')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', False)

from gui.animation import AnimationSystem
from gui.card import Card
from gui.game_layout import GameLayout
from gui.gm_label import GameMessageLabel

from kivy.app import App
from kivy.core.window import Window
from kivy.properties import NumericProperty, ObjectProperty
from durak import *
from kivy.clock import Clock, mainthread

from discovery_protocol import DiscoveryProtocol
from net_game import DurakNetGame


PORT_NO = 37020
PORT_NO_AUX = 37021


class MainLayout(FloatLayout):
    ...


class DurakFloatApp(App):
    # fixme: возможно эти свойства уже доступны через API Kivy?
    width = NumericProperty()
    height = NumericProperty()

    texture = ObjectProperty()

    def show_error(self, message):
        self.error_label.update_message(message, fade_after=3.0)

    def on_press_card(self, wcard: Card, *_):
        """
        Обработчки нажатия на любую карту
        :param wcard: виджет карты
        :param _:
        :return:
        """
        if self.locked_controls:
            self.show_error('Подождите!')
            return

        card = wcard.as_tuple
        is_my_card = wcard in self.layout.my_cards

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
                        if self.selected_card is not None:
                            self.selected_card.selected = False
                        wcard.selected = True
                        self.selected_card = wcard
                        self.show_error('Выберите карту, чтобы побить.')
                elif card in self.game.state.unbeaten_cards and self.selected_card is not None:
                    if self.game.defend(self.selected_card.as_tuple, card):
                        self.selected_card.selected = False
                        self.selected_card = None
                    else:
                        self.show_error('Вы не можете так побить!')
            else:
                self.show_error('Подождите, пока вас атакуют...')

    def on_finish_button(self, *_):
        if self.locked_controls:
            return
        r = self.game.finish_turn()
        if r == TurnFinishResult.TOOK_CARDS:
            self.show_error('Вы взяли карты!')
        self.display_whose_turn(delay=0)

    def on_disconnect_button(self, *_):
        self.reset()

    def player_take_cards(self, is_me):
        hand = self.layout.my_cards if is_me else self.layout.opp_cards
        for i, (c1, c2) in enumerate(self.layout.field):
            hand.append(c1)
            c1.opened = is_me
            if c2:
                hand.append(c2)
                c2.opened = is_me
        self.layout.field.clear()
        self.layout.update_field()
        self.update_hands()

    def update_hands(self):
        self.layout.update_cards_in_hand(is_my=True, real_cards=self.game.my_cards)
        self.layout.update_cards_in_hand(is_my=False, real_cards=self.game.opp_cards)

    def reset(self):
        if self.game:
            self.game.stop()  # остановить поток чтения и забыть игру
            self.game = None
        self.game_init = False
        self.selected_card = None
        self.locked_controls = True  # заблокировать клики по картам
        self.layout.remove_all_cards_animated()  # убрать все карты с поля
        self.toggle_buttons()

        Clock.schedule_once(self.scan, 3.0)  # начать новый поиск через некоторое время

    def show_results(self):
        """
        Показывает результат игры
        """
        if self.game:
            if self.game.winner == self.game.ME:
                self.game_label.update_message('Вы победили!')
            else:
                self.error_label.update_message('Вы проиграли!')
                self.game_label.update_message('')
        self.locked_controls = True
        self.toggle_buttons()

    @mainthread
    def on_game_state_update(self, *_):
        # синхорнизировать состояние игры и GUI
        if not self.game_init:
            self.game_init = True
            self.layout.make_cards(self.game.my_cards, self.game.opp_cards, self.game.state.trump, self.game.state.deck)

        if self.game.winner is not None:
            self.show_results()
        else:
            up = self.game.state.last_update

            print(f'update: {up}')

            action = up.get('action')
            if action == UpdateAction.ATTACK:
                card = up['card']
                self.layout.put_card_to_field(card)
            elif action == UpdateAction.DEFEND:
                att_card = up['attacking_card']
                def_card = up['defending_card']
                self.layout.put_card_to_field(def_card, att_card)
            elif action == UpdateAction.FINISH_TURN:
                if 'clear_field' in up:
                    self.layout.throw_away_field()
                else:
                    me_took = self.game.is_me(up['take_cards']['player'])
                    self.player_take_cards(me_took)

                self.layout.give_cards(up['from_deck'], len(self.game.state.deck),
                                       self.game.my_cards, self.game.opp_cards, self.game.my_index)

            self.update_hands()

            self.toggle_buttons()

            self.display_whose_turn(delay=0)

            # if not self.game.is_my_turn and not self.game.state.possible_to_beat:
            #     self.show_error("Вам придется взять карты!")

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

        self.locked_controls = False
        self.my_pid = rand_id()

        self.game: DurakNetGame = None
        self.game_init = False
        self.discovery = None
        self.selected_card = None

    def build(self):
        Builder.load_file('durak.kv')
        return MainLayout()

    def display_whose_turn(self, delay=3.0):
        def _inner(*_):
            if self.game and self.game.winner is None:
                self.game_label.update_message('Ваш ход!' if self.game.is_my_turn else 'Ход соперника!')

        Clock.schedule_once(_inner, delay)

    def toggle_button(self, button, is_on, text=''):
        """ Убирает или показывает кнопку на экране, а также обновляет ее текст """
        if text:
            button.text = text
        button.disabled = not is_on
        button.opacity = 1.0 if is_on else 0.0

    @mainthread
    def toggle_buttons(self):

        finish_active = False
        finish_text = ""
        disconnect_text = ""

        game_active = self.game is not None
        if game_active:
            can_take = self.game.state.any_unbeaten_cards and not self.game.is_my_turn
            can_finish = self.game.state.field and not self.game.state.any_unbeaten_cards and self.game.is_my_turn

            finish_active = can_take or can_finish
            finish_text = "Бито" if self.game.is_my_turn else "Взять карты!"

            if self.game.winner:
                disconnect_text = 'Новая игра!'
            else:
                disconnect_text = "Отключиться"

        self.toggle_button(self.finish_button, finish_active, finish_text)
        self.toggle_button(self.disconnect_button, game_active, disconnect_text)

    def on_start(self):
        super().on_start()

        self.width, self.height = Window.size
        self.layout = GameLayout(self.width, self.height, self.root, self.on_press_card)

        self.game_label: GameMessageLabel = self.root.ids.game_label
        self.error_label: GameMessageLabel = self.root.ids.error_label
        self.finish_button: Button = self.root.ids.finish_turn_button
        self.disconnect_button: Button = self.root.ids.disconnect_button
        self.toggle_buttons()

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
