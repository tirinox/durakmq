from math import sin, pi, cos

from kivy.clock import Clock
from kivy.uix.widget import Widget

from gui.card import Card
from util import rand_circle_pos


class GameLayout:
    def pos_of_hand(self, i, n, is_my):
        """
        Положение карты в руке
        :param i: номер карты с 0 слева направо
        :param n: количество карт в руке
        :param is_my: True в моей руке (по дуге снизу), False в руке соперника (по дуге сверху) 
        :return: x, y, поровот
        """
        r = 0.9 * self.width
        cx = self.width * 0.5
        cy = -0.8 * r if is_my else self.height + 0.8 * r

        d_ang = 10
        max_ang = min(30, d_ang * n / 2)
        min_ang = -max_ang

        ang = min_ang + (max_ang - min_ang) / (n + 1) * (i + 1)
        ang_r = ang / 180 * pi
        m = 1 if is_my else -1
        return cx + r * sin(ang_r), cy + m * r * cos(ang_r), -m * ang

    def pos_of_trump(self):
        """
        Положение козыря
        :return: x, y, поворот
        """
        return self.width * 0.83, self.height / 2, 90

    def pos_of_deck(self):
        """
        Положение колоды
        :return: x, y, поворот
        """
        return self.width * 0.93, self.height / 2, 0

    def pos_of_field_cell(self, i, n, beneath):
        """
        Положение карты на поле
        :param i: номер стопки слева направо 
        :param n: количество стопок
        :param beneath: под низом ли?
        :return: x, y, поворот 
        """"""
        """
        x_step = self.width * 0.15
        x_start = self.width * 0.12
        width = x_start + x_step * n
        if width >= self.width * 0.8:
            x_step = (self.width * 0.8 - x_start) / (n + 1)
        ang = -10.0 if beneath else 10.0
        x = x_start + i * x_step
        y = self.height * 0.5 + (-0.04 if beneath else 0.04) * self.height
        return x, y, ang

    def make_card(self, card, attrs=(0, 0, 0), opened=True):
        card = tuple(card)
        wcard = Card.make(card, opened=opened)
        wcard.set_animated_targets(*attrs)
        wcard.on_press = lambda *_: self.press_handler(wcard)
        self.card2widget[card] = wcard
        self.root.add_widget(wcard)
        return wcard

    def give_cards(self, card_array: list, deck_len, my_cards, opp_cards, my_index):
        def give_one_card(*_):
            player_index, card = card_array.pop(0)
            took_last = deck_len == 0
            give_trump = took_last and len(card_array) == 0
            for_me = player_index == my_index
            hand = self.my_cards if for_me else self.opp_cards

            if give_trump:
                # последняя карта - открытый козырь
                self.trump_card.opened = for_me
                hand.append(self.trump_card)
                self.trump_card = None
            elif self.trump_card:
                wcard = self.make_card(card, opened=for_me)
                wcard.set_immeditate_attr(*self.pos_of_deck())
                hand.append(wcard)

            self.update_cards_in_hand(is_my=True, real_cards=my_cards)
            self.update_cards_in_hand(is_my=False, real_cards=opp_cards)
            self.update_deck(deck_len + len(card_array))

            if not card_array:
                # кончились карты - прекратим давать и вернем управление
                Clock.unschedule(give_one_card)
                self.locked_controls = False

        if card_array:
            self.locked_controls = True
            Clock.schedule_interval(give_one_card, 0.3)

    @property
    def field_card_widgets(self):
        return [c for pair in self.field for c in pair if c is not None]

    def throw_away_field(self, *_):
        for c in self.field_card_widgets:
            self.throw_away_card(c)
        self.field.clear()

    def put_card_to_field(self, card, on_card=None):
        card = tuple(card)
        wcard = self.card2widget.get(card, None)
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

        self.update_field()

    def update_deck(self, n):
        self.deck_card.counter = n
        if self.deck_card.counter <= 0:
            # сдвинуть за экран, если кончились карт
            self.deck_card.set_animated_targets(1.5 * self.width, 0.5 * self.height, 0)

    def update_cards_in_hand(self, is_my, real_cards):
        """
        Сортирует карты в руке игрока или соперника сообразно порядку в игре
        После сортировки устанавливаются для каждой карты ее позиция и поворот
        """
        # реальный порядок карт в руке задается внутри класса Durak, нам при сортировке карт в руке нужно его соблюсти
        n = len(real_cards)
        for i, card in enumerate(real_cards):
            wcard = self.card2widget.get(card, None)
            if wcard:
                wcard.bring_to_front()  # чтобы каждая следующая была поверх предыдущей
                wcard.set_animated_targets(*self.pos_of_hand(i, n, is_my))

    def update_field(self):
        n = len(self.field)
        for i, (c1, c2) in enumerate(self.field):
            c1.set_animated_targets(*self.pos_of_field_cell(i, n, beneath=True))
            if c2:
                c2.set_animated_targets(*self.pos_of_field_cell(i, n, beneath=False))

    def make_cards(self, my_cards, opp_cards, trump, deck):
        self.card2widget = {}
        for card in my_cards:
            wcard = self.make_card(card)
            self.my_cards.append(wcard)

        for card in opp_cards:
            wcard = self.make_card(card, opened=False)
            self.opp_cards.append(wcard)

        self.update_field()

        self.trump_card = self.make_card(trump, self.pos_of_trump())
        self.deck_card = self.make_card(('', ''), self.pos_of_deck())
        self.update_deck(len(deck))

    def destory_card(self, wcard: Card):
        wcard.destroy_card_after_delay(1.0)
        del self.card2widget[wcard.as_tuple]

    def throw_away_card(self, wcard: Card):
        if wcard is not None:
            wcard.set_animated_targets(-self.width, self.height * 0.5, 0)
            self.destory_card(wcard)

    def remove_all_cards_animated(self):
        for wcard in list(self.card2widget.values()):
            if wcard:
                wcard.set_animated_targets(*rand_circle_pos(), 0)
                self.destory_card(wcard)
        self.card2widget = {}
        self.field.clear()

    def __init__(self, width, height, root: Widget, press_handler):
        self.width = width
        self.height = height

        self.card2widget = {}
        self.field = []
        self.my_cards = []
        self.opp_cards = []
        self.def_card = None
        self.trump_card = None
        self.deck_card = None

        self.press_handler = press_handler

        self.root = root
