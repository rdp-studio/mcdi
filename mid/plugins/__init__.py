from mid.core import BaseGenerator


class Plugin(object):
    __dependencies__ = []
    __conflicts__ = []

    __author__ = "undefined"

    def exec(self, generator: BaseGenerator):
        pass

    def init(self, generator: BaseGenerator):
        pass
