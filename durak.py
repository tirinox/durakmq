import random

# масти
from enum import Enum

SPADES = '♠'
HEARTS = '♥'
DIAMS = '♦'
CLUBS = '♣'
SUITS = [SPADES, HEARTS, DIAMS, CLUBS]

# достоинтсва карт
ACE = 'A'
NOMINALS = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', ACE]
NOMINALS_SHORT = ['J', 'Q', 'K', ACE]

# поиск индекса по достоинству
NAME_TO_VALUE = {n: i for i, n in enumerate(NOMINALS)}

# карт в руке при раздаче
CARDS_IN_HAND_MAX = 6

N_PLAYERS = 2

# эталонная колода (каждая масть по каждому номиналу) - 36 карт
DECK = [(nom, suit) for nom in NOMINALS for suit in SUITS]
DECK_SHORT = [(nom, suit) for nom in NOMINALS_SHORT for suit in SUITS]


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
        lack = max(0, CARDS_IN_HAND_MAX - len(self.cards))  # сколько не хватает
        n = min(len(deck), lack)
        new_cards = deck[:n]  # первые n карт сверхку колоды
        self.add_cards(new_cards)
        del deck[:n]
        return new_cards

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


class TurnFinishResult(Enum):
    CANT_FORCE_TO_TAKE = 0
    UNBEATEN_CARDS = 1
    GAME_OVER = 2
    TOOK_CARDS = 3
    NORMAL_TURN = 4
    EMPTY = 5
    CANT_TAKE_NOW = 6


class UpdateAction:
    FINISH_TURN = 'finish_turn'
    ATTACK = 'attack'
    DEFEND = 'defend'


class Durak:
    def get_trump(self):
        return next(card for card in self.deck if card[0] != ACE)

    def __init__(self, rng: random.Random = None, deck=None):
        self.attacker_index = 0  # индекс атакующего игрока

        self.rng = rng or random.Random()  # генератор случайных чисел

        self.deck = deck if deck is not None else list(DECK)  # копируем колоду
        self.rng.shuffle(self.deck)  # мешаем карты в копии колоды
        # !!! верх колоды = индекс 0, низ колоды - последний в списке

        # создаем игроков и раздаем им по 6 карт из перемешанной колоды
        self.players = [Player(i, []) for i in range(N_PLAYERS)]
        for player in self.players:
            player.take_cards_from_deck(self.deck)

        # козырь - карта сверху (не туз)
        self.trump = next(card for card in self.deck if card[0] != ACE)
        # подсунем под низ
        self.deck.remove(self.trump)
        self.deck.append(self.trump)  # самый последний элемент - низ колоды

        # игровое поле: ключ - атакующая карта, значения - защищающаяся или None
        self.field = {}

        self.winner = None  # индекс победителя

        self.last_update = {}  # последние обновление

    def card_match(self, card1, card2):
        if card1 is None or card2 is None:
            return False
        n1, _ = card1
        n2, _ = card2
        return n1 == n2

    @property
    def trump_suit(self):
        return self.trump[1]

    def can_beat(self, att_card, def_card):
        """
        Бьет ли att_card карту def_card
        """
        nom1, suit1 = att_card
        nom2, suit2 = def_card

        # преобразуем строку-достоинство в численные характеристики
        nom1 = NAME_TO_VALUE[nom1]
        nom2 = NAME_TO_VALUE[nom2]

        if suit2 == self.trump_suit:
            # если козырь, то бьет любой некозырь или козырь младше
            return suit1 != self.trump_suit or nom2 > nom1
        elif suit1 == suit2:
            # иначе должны совпадать масти и номинал второй карты старше первой
            return nom2 > nom1
        else:
            return False

    def can_add_to_field(self, card):
        if not self.defending_player.cards:  # нельзя подкинуть, если у противника кончились карты!
            return False

        if not self.field:
            # на пустое поле можно ходить любой картой
            return True

        # среди всех атакующих и отбивающих карт ищем совпадения
        for attack_card, defend_card in self.field.items():
            if self.card_match(attack_card, card) or self.card_match(defend_card, card):
                return True

        return False

    @property
    def possible_to_beat(self):
        """
        Проверяет можно ли вообще обить что-то в такой ситуации
        """
        for unbeaten_card in self.unbeaten_cards:
            can_beat = any(self.can_beat(my_card, unbeaten_card) for my_card in self.defending_player.cards)
            if not can_beat:
                return False
        return True

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
    def unbeaten_cards(self):
        return [c for c in self.field.keys() if self.field[c] is None]

    @property
    def attacking_player(self):
        return self.players[self.attacker_index]

    @property
    def defending_player(self):
        return self.players[(self.attacker_index + 1) % N_PLAYERS]

    def defend_variants(self, card):
        """
        Варианты, какие карты можно побить
        :param card: карта, которой бьем
        :return: карты, которые можно отбить
        """
        return [att_card for att_card in self.unbeaten_cards if self.can_beat(att_card, card)]

    def _take_all_field(self):
        """
        Соперник берет все катры со стола себе.
        """
        cards = self.attacking_cards + self.defending_cards
        self.defending_player.add_cards(cards)
        self.field = {}
        self.last_update['take_cards'] = {
            'cards': cards,
            'player': self.defending_player.index
        }

    @property
    def any_unbeaten_cards(self):
        return len(self.unbeaten_cards)

    # ---- ДЕЙСТВИЯ -----

    def attack(self, card):
        if self.winner:  # игра не должна быть окончена!
            return False

        if card not in self.attacking_player.cards:
            return False

        # можно ли добавить эту карту на поле? (по масти или достоинству)
        if not self.can_add_to_field(card):
            return False

        self.attacking_player.take_card(card)  # уберем карту из руки атакующего
        self.field[card] = None  # карта добавлена на поле, пока не бита

        self.last_update = {
            'action': UpdateAction.ATTACK,
            'card': card,
            'player': self.attacker_index
        }

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
            self.defending_player.take_card(defending_card)

            self.last_update = {
                'action': UpdateAction.DEFEND,
                'defending_card': defending_card,
                'attacking_card': attacking_card,
                'player': self.defending_player.index
            }

            return True
        return False

    def finish_turn(self) -> TurnFinishResult:
        assert not self.winner

        self.last_update = {
            'action': UpdateAction.FINISH_TURN
        }

        took_cards = False
        if self.any_unbeaten_cards:
            # забрать все карты, если игрок не отбился в момент завершения хода
            self._take_all_field()
            took_cards = True
        else:
            # бито! очищаем поле (отдельного списка для бито нет, просто удаляем карты)
            self.field = {}
            self.last_update['clear_field'] = True

        # очередность взятия карт из колоды определяется индексом атакующего (можно сдвигать на 1, или нет)
        take_cards = []
        for p in rotate(self.players, self.attacker_index):
            cards = p.take_cards_from_deck(self.deck)
            take_cards += [(p.index, card) for card in cards]
        self.last_update['from_deck'] = take_cards

        # колода опустела?
        if not self.deck:
            for p in self.players:
                if not p.cards:  # если у кого-то кончились карты, он победил!
                    self.winner = p.index
                    self.last_update['winner'] = self.winner
                    return TurnFinishResult.GAME_OVER

        if took_cards:
            return TurnFinishResult.TOOK_CARDS
        else:
            # переход хода, если не отбился
            self.attacker_index = self.defending_player.index
            self.last_update['turn_change'] = self.attacker_index
            return TurnFinishResult.NORMAL_TURN
