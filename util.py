import random
from math import cos, pi, sin


def rand_id():
    return random.getrandbits(64)


def rand_circle_pos(r=3000):
    angle = random.uniform(0, 2 * pi)
    return r * sin(angle), r * cos(angle)


def debug_start():
    import os
    from kivy.config import Config

    x = os.environ.get('x', 50)
    y = os.environ.get('y', 50)

    Config.set('graphics', 'position', 'custom')
    Config.set('graphics', 'left', x)
    Config.set('graphics', 'top', y)
