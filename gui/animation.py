from kivy.clock import Clock
from kivy.uix.widget import Widget


def fast_dist(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


class AnimationSystem:
    EXP_ATT = 5.0

    def update(self, dt):
        df = self.EXP_ATT * dt
        for child in self.widget.children:
            if hasattr(child, 'target_position'):
                x, y = child.pos
                # компенсируем положение точки, смещая ее из нижнего левого угла в середину виджета
                x += child.size[0] / 2
                y += child.size[1] / 2
                tx, ty = child.target_position
                if fast_dist(x, y, tx, ty) >= 0.1:
                    x += (tx - x) * df
                    y += (ty - y) * df
                    # возвращаем обратно из середины точку к углу
                    child.pos = (x - child.size[0] / 2, y - child.size[1] / 2)
            if hasattr(child, 'target_rotation'):
                tr, r = child.target_rotation, child.rotation
                if abs(tr - r) >= 0.1:
                    child.rotation += (tr - r) * df

    def __init__(self, w: Widget):
        self.widget = w

    def run(self):
        Clock.schedule_interval(self.update, 1.0 / 60.0)
