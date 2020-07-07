import random

# масти
SPADES = '♠'
HEARTS = '♥'
DIAMS = '♦'
CLUBS = '♣'

# достоинтсва карт
NOMINALS = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

# поиск индекса по достоинству
NAME_TO_VALUE = {n: i for i, n in enumerate(NOMINALS)}

# карт в руке при раздаче
CARDS_IN_HAND_MAX = 6

N_PLAYERS = 2

# эталонная колода (каждая масть по каждому номиналу) - 36 карт
DECK = [(nom, suit) for nom in NOMINALS for suit in [SPADES, HEARTS, DIAMS, CLUBS]]


class Player:
    def __init__(self, index, cards):
        self.index = index
        self.cards = list(map(tuple, cards))  # убедимся, что будет список кортежей

    def take_cards_from_deck(self, deck: list):
        """
        Взять недостающее количество карт из колоды
        Колода уменьшится
        :param deck: список карт колоды
        """
        lack = max(0, CARDS_IN_HAND_MAX - len(self.cards))
        n = min(len(deck), lack)
        self.add_cards(deck[:n])
        del deck[:n]
        return self

    def sort_hand(self):
        """
        Сортирует карты по достоинству и масти
        """
        self.cards.sort(key=lambda c: (NAME_TO_VALUE[c[0]], c[1]))
        return self

    def add_cards(self, cards):
        self.cards += list(cards)
        self.sort_hand()
        return self

    # всякие вспомогательные функции:

    def __repr__(self):
        return f"Player{self.cards!r}"

    def take_card(self, card):
        self.cards.remove(card)

    @property
    def n_cards(self):
        return len(self.cards)

    def __getitem__(self, item):
        return self.cards[item]


def rotate(l, n):
    return l[n:] + l[:n]


class Durak:
    def __init__(self, rng: random.Random = None):
        self.attacker_index = 0  # индекс атакующего игрока

        self.rng = rng or random.Random()  # генератор случайных чисел

        self.deck = list(DECK)  # копируем колоду
        self.rng.shuffle(self.deck)  # мешаем карты в копии колоды

        # создаем игроков и раздаем им по 6 карт из перемешанной колоды
        self.players = [Player(i, []).take_cards_from_deck(self.deck)
                        for i in range(N_PLAYERS)]

        # козырь - карта сверху
        self.trump = self.deck[0][1]
        # кладем козырь под низ вращая список по кругу на 1 назад
        self.deck = rotate(self.deck, -1)

        # игровое поле: ключ - атакующая карта, значения - защищающаяся или None
        self.field = {}

        self.winner = None  # индекс победителя

    def card_match(self, card1, card2):
        if card1 is None or card2 is None:
            return False
        n1, _ = card1
        n2, _ = card2
        return n1 == n2

    def can_beat(self, card1, card2):
        """
        Бьет ли card1 карту card2
        """
        nom1, suit1 = card1
        nom2, suit2 = card2

        # преобразуем строку-достоинство в численные характеристики
        nom1 = NAME_TO_VALUE[nom1]
        nom2 = NAME_TO_VALUE[nom2]

        if suit2 == self.trump:
            # если козырь, то бьет любой некозырь или козырь младше
            return suit1 != self.trump or nom2 > nom1
        elif suit1 == suit2:
            # иначе должны совпадать масти и номинал второй карты старше первой
            return nom2 > nom1
        else:
            return False

    def can_add_to_field(self, card):
        if not self.field:
            # на пустое поле можно ходить любой картой
            return True

        # среди всех атакующих и отбивающих карт ищем совпадения
        for attack_card, defend_card in self.field.items():
            if self.card_match(attack_card, card) or self.card_match(defend_card, card):
                return True

        return False

    @property
    def attacking_cards(self):
        """
        Список атакующих карт
        """
        return list(filter(bool, self.field.keys()))

    @property
    def defending_cards(self):
        """
        Список отбивающих карт (фильртруем None)
        """
        return list(filter(bool, self.field.values()))

    @property
    def current_player(self):
        return self.players[self.attacker_index]

    @property
    def opponent_player(self):
        return self.players[(self.attacker_index + 1) % N_PLAYERS]

    def attack(self, card):
        assert not self.winner  # игра не должна быть окончена!

        # можно ли добавить эту карту на поле? (по масти или достоинству)
        if not self.can_add_to_field(card):
            return False
        cur, opp = self.current_player, self.opponent_player
        cur.take_card(card)  # уберем карту из руки атакующего
        self.field[card] = None  # карта добавлена на поле, пока не бита
        return True

    def defend(self, attacking_card, defending_card):
        """
        Защита
        :param attacking_card: какую карту отбиваем
        :param defending_card: какой картой защищаемя
        :return: bool - успех или нет
        """
        assert not self.winner  # игра не должна быть окончена!

        if self.field[attacking_card] is not None:
            # если эта карта уже отбита - уходим
            return False
        if self.can_beat(attacking_card, defending_card):
            # еслии можем побить, то кладем ее на поле
            self.field[attacking_card] = defending_card
            # и изымаем из руки защищающегося
            self.opponent_player.take_card(defending_card)
            return True
        return False

    def defend_variants(self, card):
        unbeaten_cards = [c for c in self.field.keys() if self.field[c] is None]
        return [i for i, att_card in enumerate(unbeaten_cards) if self.can_beat(att_card, card)]

    # константы результатов хода
    NORMAL = 'normal'
    TOOK_CARDS = 'took_cards'
    GAME_OVER = 'game_over'

    @property
    def any_unbeaten_cards(self):
        return any(def_card is None for def_card in self.field.values())

    def finish_turn(self):
        assert not self.winner

        took_cards = False
        if self.any_unbeaten_cards:
            # забрать все карты, если игрок не отбился в момент завершения хода
            self._take_all_field()
            took_cards = True
        else:
            # бито! очищаем поле (отдельного списка для бито нет, просто удаляем карты)
            self.field = {}

        # очередность взятия карт из колоды определяется индексом атакующего (можно сдвигать на 1, или нет)
        for p in rotate(self.players, self.attacker_index):
            p.take_cards_from_deck(self.deck)

        # колода опустела?
        if not self.deck:
            for p in self.players:
                if not p.cards:  # если у кого-то кончились карты, он победил!
                    self.winner = p.index
                    return self.GAME_OVER

        if took_cards:
            return self.TOOK_CARDS
        else:
            # переход хода, если не отбился
            self.attacker_index = self.opponent_player.index
            return self.NORMAL

    def _take_all_field(self):
        """
        Соперник берет все катры со стола себе.
        """
        cards = self.attacking_cards + self.defending_cards
        self.opponent_player.add_cards(cards)
        self.field = {}
