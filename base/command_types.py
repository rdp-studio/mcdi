class Position(object):
    def __init__(self, x, y, z):
        self.position = str(x), str(y), str(z)

    def __str__(self):
        return "\x20".join(self.position)


class RelativePosition(object):
    def __init__(self, x=0, y=0, z=0):
        self.position = f"~{x:.6f}", f"~{y:.6f}", f"~{z:.6f}"

    def __str__(self):
        return "\x20".join(self.position)


class LocalPosition(object):
    def __init__(self, x=0, y=0, z=0):
        self.position = f"^{x:.6f}", f"^{y:.6f}", f"^{z:.6f}"

    def __str__(self):
        return "\x20".join(self.position)


class Command(object):
    def __init__(self, command):
        self.__command = command

    def __str__(self):
        return self.__command


class Function(Command):
    def __init__(self, namespace="mcdi", func="func"):
        super(Function, self).__init__(
            f"function {namespace}:{func}"
        )


class Reload(Command):
    def __init__(self):
        super(Reload, self).__init__(
            "reload"
        )


class Execute(Command):
    def __init__(self, command, as_=None, at=None, positioned=None):
        string = "execute\x20"
        if as_ is not None:  # Run as entity
            string += f"as\x20{as_}\x20"
        if at is not None:  # Run at entity
            string += f"at\x20{at}\x20"
        if positioned is not None:  # Run at position
            string += f"positioned\x20{positioned}\x20"

        super(Execute, self).__init__(
            string + f"run\x20{command}"
        )


class PlaySound(Command):
    def __init__(self, resource, channel="voice", for_="@s", position=RelativePosition(), velocity=1, pitch=1):
        super(PlaySound, self).__init__(
            f"playsound {resource} {channel} {for_} {position} {velocity} {pitch}"
        )


class StopSound(Command):
    def __init__(self, resource, channel="voice", for_="@s"):
        super(StopSound, self).__init__(
            f"stopsound {for_} {channel} {resource}"
        )
