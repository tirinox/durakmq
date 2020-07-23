from kivy.uix.popup import Popup


class MyPopup(Popup):
    @classmethod
    def show(cls, title, text):
        p = MyPopup()
        # p.title = title
        # p.ids.label.text = text
        p.open()


def fast_dist(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)
