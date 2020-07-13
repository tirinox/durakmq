from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty
from durak import *


Window.size = (540, 960)  # разрешение экрана аля смартфон


# from kivy.uix.behaviors import ButtonBehavior


class Card(Button):
    nominal = StringProperty(NOMINALS[0])
    suit = StringProperty(SPADES)



class DurakKivyApp(App):
    ...
    # def build(self):
    #     # self.win_size = Window.size
    #
    #     card = Button()
    #     card.text = "efefef"
    #
    #     card.pos = (100, 100)
    #
    #     layout = FloatLayout()
    #     layout.add_widget(card)
    #     return layout


if __name__ == '__main__':
    DurakKivyApp().run()
