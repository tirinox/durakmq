from math import sin, pi, cos

from gui.card import Card


class GameLayout:
    def attr_to_my_hand(self, i, n):
        """
        Положение карт в моей руке (по дуге снизу)
        """
        r = 0.9 * self.width
        cx, cy = (self.width * 0.5, -0.8 * r)
        min_ang, max_ang = -30, 30
        ang = min_ang + (max_ang - min_ang) / (n + 1) * i
        ang_r = ang / 180 * pi
        return cx + r * sin(ang_r), cy + r * cos(ang_r), -ang

    def attr_to_opp_hand(self, i, n):
        """
        Положение карт в руке соперника (по дуге сверху)
        """
        r = 0.9 * self.width
        cx, cy = (self.width * 0.5, self.height + 0.8 * r)
        min_ang, max_ang = -30, 30
        ang = min_ang + (max_ang - min_ang) / (n + 1) * i
        ang_r = ang / 180 * pi
        return cx + r * sin(ang_r), cy - r * cos(ang_r), ang

    def attr_to_trump(self):
        return self.width * 0.83, self.height / 2, 90

    def attr_to_deck(self):
        return self.width * 0.93, self.height / 2, 0

    def attr_to_field(self, i, n, beneath):
        x_step = self.width * 0.15
        x_start = self.width * 0.12
        width = x_start + x_step * n
        if width >= self.width * 0.8:
            x_step = (self.width * 0.8 - x_start) / (n + 1)
        ang = -10.0 if beneath else 10.0
        x = x_start + i * x_step
        y = self.height * 0.5 + (-0.04 if beneath else 0.04) * self.height
        return x, y, ang

    def throw_away_card(self, w: Card):
        if w is not None:
            w.set_animated_targets(-self.width, self.height * 0.5, 0)
            w.destroy_card_after_delay(1.0)

    def __init__(self, width, height):
        self.width = width
        self.height = height
