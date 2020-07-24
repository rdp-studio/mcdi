from mid.core import Generator


class Middleware(object):
    def __init__(self):
        pass

    def exec(self, generator: Generator) -> None:
        pass

    def init(self, generator: Generator) -> None:
        pass
