class Command(object):
    def __init__(self, command):
        self.__command = command

    def __str__(self):
        return self.__command


class Function(Command):
    def __init__(self, namespace="mcdi", func="func"):
        super().__init__(f"function {namespace}:{func}")


class Reload(Command):
    def __init__(self):
        super().__init__("reload")
