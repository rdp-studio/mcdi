from abc import abstractmethod

from mid.core import Generator


class Middle(object):
    __dependencies__ = []
    __conflicts__ = []

    __author__ = "undefined"

    @abstractmethod
    def exec(self, generator: Generator) -> None:
        pass

    @abstractmethod
    def init(self, generator: Generator) -> None:
        pass

    @abstractmethod
    def dependency_connect(self, dependencies):
        pass
