class Command(object):
    pass


class Function(Command):
    def __init__(self, namespace="mcdi", func="func"):
        super().__init__()
        self.__command = f"function {namespace}:{func}"

    def __str__(self):
        return self.__command


class Reload(Command):
    def __init__(self):
        super().__init__()
        self.__command = "reload"

    def __str__(self):
        return self.__command
