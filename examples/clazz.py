import sys, os

root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(root))

from tracing import hook


class Clazz:
    def __init__(self, x, y):
        self.x = x
        self.y = y


@hook
def main():
    clazz = Clazz(1, 2)
