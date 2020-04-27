__author__ = "kworker"
__doc__ = """Fix the volume issues for the soma pack."""


class MainObject(object):
    def __init__(self, *args, **kwargs):
        self.mappings = kwargs
        pass

    def execute(self, generator):
        if not generator.parsed_msgs:
            return None
        msg = generator.parsed_msgs[-1]
        if (ch := str(msg["ch"])) in self.mappings.keys():
            factor = self.mappings[ch]
            msg["v"] = msg["v"] * factor
