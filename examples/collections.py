import sys, os

root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(root))

from tracing import entrypoint, register


def magic():
    return None


@register()
def make_collections():
    l = list()
    l.append(1)
    l.append("string")

    s = set()
    s.add(1)
    s.add("string")
    s.add("string")

    d = dict()
    d["a"] = 1
    d["b"] = 2

    another_collection = magic()

    return d

@entrypoint()
def main():
    ...