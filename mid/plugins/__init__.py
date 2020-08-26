from abc import abstractmethod

from mid.core import BaseGenerator


class Plugin(object):
    __dependencies__ = []
    __conflicts__ = []

    __author__ = "undefined"

    @abstractmethod
    def exec(self, generator: BaseGenerator):
        pass

    @abstractmethod
    def init(self, generator: BaseGenerator):
        pass

    @abstractmethod
    def dependency_connect(self, dependencies):
        pass
