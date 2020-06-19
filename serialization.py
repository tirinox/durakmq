from durak import Durak, Player


def serialize_recursive(o):
    if hasattr(o, '__dict__'):
        return {k: serialize_recursive(v) for k, v in o.__dict__.items()}
    elif isinstance(o, (tuple, list)):
        return [serialize_recursive(v) for v in o]
    else:
        return o


class DurakSerialized(Durak):
    def __init__(self, j=None):
        super().__init__()
        self.game_id = None
        if j is not None:
            for name in self.__dict__:
                if name in j:
                    setattr(self, name, j[name])
            self.players = [Player(p['index'], p['cards']) if isinstance(p, dict) else p for p in self.players]
            self.deck = list(map(tuple, self.deck))

    def serialized(self):
        return serialize_recursive(self)
