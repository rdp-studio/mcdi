from gsmidi.core import Generator


class Middleware(object):
    __dependencies__ = []
    __conflicts__ = []

    def __init__(self):
        pass

    def exec(self, generator: Generator) -> None:
        pass

    def init(self, generator: Generator) -> None:
        pass
