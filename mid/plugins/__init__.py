from abc import abstractmethod

from mid.core import BaseCbGenerator


class Plugin(object):
    __dependencies__ = []
    __conflicts__ = []

    __author__ = "undefined"

    @abstractmethod
    def exec(self, generator: BaseCbGenerator):
        pass

    @abstractmethod
    def init(self, generator: BaseCbGenerator):
        pass

    @abstractmethod
    def dependency_connect(self, dependencies):
        pass
