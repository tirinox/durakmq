import random
from math import cos, pi, sin


def rand_id():
    return random.getrandbits(64)


def rand_circle_pos(r=2000):
    angle = random.uniform(0, 2 * pi)
    return r * sin(angle), r * cos(angle)
