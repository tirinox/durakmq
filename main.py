from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from durak import *


Window.size = (540, 960)  # разрешение экрана аля смартфон


from kivy.uix.behaviors import ButtonBehavior


class Card(Button):
    nominal = StringProperty(NOMINALS[0])
    suit = StringProperty(DIAMS)
    opened = BooleanProperty(True)
    counter = NumericProperty(-1)

    def set_c(self, *args):
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
        self.bind(suit=self.set_c)
        self.bind(nominal=self.set_c)
        self.bind(opened=self.set_c)
        self.bind(counter=self.set_c)


class DurakKivyApp(App):
    width = NumericProperty()
    height = NumericProperty()

    def on_start(self):
        super().on_start()
        self.width, self.height = Window.size

        opp_cards = self.root.ids.opp_cards
        card = Card()
        card.nominal = NOMINALS[2]
        card.suit = CLUBS
        opp_cards.add_widget(card)

        card = Card()
        card.nominal = NOMINALS[7]
        card.suit = DIAMS
        card.opened = False
        opp_cards.add_widget(card)


if __name__ == '__main__':
    DurakKivyApp().run()
