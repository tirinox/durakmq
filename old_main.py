from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from durak import *


PORT_NO = 37020
PORT_NO_AUX = 37021

Window.size = (540, 960)  # разрешение экрана аля смартфон


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
        # fixme: можно ли обойтись без bind?
        self.bind(suit=self.set_c)
        self.bind(nominal=self.set_c)
        self.bind(opened=self.set_c)
        self.bind(counter=self.set_c)


class MyPopup(Popup):
    @classmethod
    def show(cls, title, text):
        p = MyPopup()
        p.title = title
        p.ids.label.text = text
        p.open()


class DurakKivyApp(App):
    # fixme: возможно эти свойства уже доступны через API Kivy?
    width = NumericProperty()
    height = NumericProperty()

    def _tap_card(self, card, widget):
        print(card)
        self._remove_card_from_hand(card, widget.opened)
        MyPopup.show('Ура', f'убрали карту {card}')

    def _make_card(self, card, opened=True):
        card_widget = Card()
        card_widget.nominal, card_widget.suit = card
        card_widget.opened = opened
        card_widget.on_press = lambda: self._tap_card(card, card_widget)
        return card_widget

    def _get_container(self, card_widget):
        return self._my_cards if card_widget.opened else self._opp_cards

    def _push_card_to_hand(self, card):
        self._get_container(card).add_widget(card)

    def _remove_card_from_hand(self, card, is_my):
        container = self._my_cards if is_my else self._opp_cards
        for cw in container.children:
            if (cw.nominal, cw.suit) == card:
                cw.parent.remove_widget(cw)

    def _set_deck(self, trump, count_left):
        td = self._trump_and_deck
        td.clear_widgets()
        td.add_widget(self._make_card(trump))
        if count_left > 0:
            deck = Card()
            deck.counter = count_left
            td.add_widget(deck)

    def on_start(self):
        super().on_start()
        self.width, self.height = Window.size

        self._opp_cards: Widget = self.root.ids.opp_cards
        self._my_cards: Widget = self.root.ids.my_cards
        self._field: Widget = self.root.ids.field
        self._trump_and_deck: Widget = self.root.ids.trump_and_deck
        self._status_bar: Label = self.root.ids.status_bar

        self._status_bar.text = 'Ищем сопрника!'

        deck = list(DECK)
        random.shuffle(deck)
        for i in range(CARDS_IN_HAND_MAX):
            self._push_card_to_hand(self._make_card(deck.pop(), True))
            self._push_card_to_hand(self._make_card(deck.pop(), False))
        self._set_deck(deck.pop(), len(deck))


if __name__ == '__main__':
    DurakKivyApp().run()
