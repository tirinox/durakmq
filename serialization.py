from durak import Durak, Player


class DurakSerialized(Durak):
    def __init__(self, j=None):
        if j is None:
            super().__init__()
        else:
            # десериализация
            self.trump = j["trump"]
            self.attacker_index = j["attacker_index"]
            self.players = [Player(p['index'], p['cards']) for p in j["players"]]
            self.deck = list(map(tuple, j["deck"]))
            self.winner = j["winner"]
            # в Python ключем словаря может быть кортеж, а в JSON - нет,
            # поэтому собираем поле из массива пар ключ-значение [ [к1, зн1], [к2, зн2] ]
            self.field = {tuple(ac): tuple(dc) if dc is not None else None for ac, dc in j["field"]}
            self.last_update = j["last_update"]

    def serialized(self):
        # сериализация
        j = {
            "trump": self.trump,
            "attacker_index": self.attacker_index,
            "deck": self.deck,
            "winner": self.winner,
            "field": list(self.field.items()),  # преобразуем словарь в список пар (ключ, значение)
            "players": [
                {
                    "index": p.index,
                    "cards": p.cards
                } for p in self.players
            ],
            "last_update": self.last_update
        }
        return j
