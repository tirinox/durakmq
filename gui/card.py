from kivy.uix.button import Button
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from durak import NOMINALS, DIAMS, HEARTS

PORT_NO = 37020
PORT_NO_AUX = 37021


class Card(Button):
    nominal = StringProperty()
    suit = StringProperty()
    opened = BooleanProperty(True)
    counter = NumericProperty(-1)
    rotation = NumericProperty(0)

    def update_text(self):
        if self.counter >= 0:
            self.text = str(int(self.counter))
            self.color = (0, 0, 0, 1)
        elif not self.opened:
            self.text = '?'
            self.color = (0, 0.5, 0, 1)
        else:
            self.text = f'{self.suit}\n{self.nominal}\n{self.suit}'
            self.color = (0.8, 0, 0, 1) if self.suit in (DIAMS, HEARTS) else (0, 0, 0, 1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.target_position = (100, 100)
        self.target_rotation = 0

    @classmethod
    def make(cls, card, opened=True):
        card_widget = Card()
        card_widget.nominal, card_widget.suit = card
        card_widget.opened = opened
        card_widget.update_text()
        # card_widget.on_press = lambda: self._tap_card(card, card_widget)
        return card_widget


