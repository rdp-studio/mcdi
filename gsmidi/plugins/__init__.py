from gsmidi.core import Generator


class Plugin(object):
    __dependencies__ = []
    __conflicts__ = []

    def exec(self, generator: Generator):
        pass

    def init(self, generator: Generator):
        pass
