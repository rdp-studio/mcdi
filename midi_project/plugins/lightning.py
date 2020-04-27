__author__ = "kworker"
__doc__ = """君指先跃动の光は、私の一生不変の信仰に、唯私の超电磁炮永生き！"""


class MainObject(object):
    def __init__(self, *args, **kwargs):
        pass

    @staticmethod
    def execute(generator):
        generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index, z_shift=generator.wrap_index,
                                       command="summon lightning_bolt")
        generator.y_index += 1
