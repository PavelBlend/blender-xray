
class Chunks:
    HEADER = 0x0
    MESHES = 0x1
    SLOTS = 0x2


class LevelDetails:
    pass


class DetailsHeader:

    class Transform:
        def __init__(self):
            self.x = None
            self.y = None

    def __init__(self):
        self.format_version = None
        self.slot_size = 2.0
        self.slot_half = self.slot_size / 2
        self.meshes_count = None
        self.offset = self.Transform()
        self.size = self.Transform()
        self.slots_count = 0

    def calc_slots_count(self):
        self.slots_count = self.size.x * self.size.y


FORMAT_VERSION_2 = 2
FORMAT_VERSION_3 = 3
SUPPORT_FORMAT_VERSIONS = (FORMAT_VERSION_2, FORMAT_VERSION_3)

PIXELS_OFFSET_1 = {
    0: (0, 0),
    1: (1, 0),
    2: (0, 1),
    3: (1, 1),
    }

PIXELS_OFFSET_2 = {
    0: (0, 1),
    1: (1, 1),
    2: (0, 0),
    3: (1, 0),
    }

DENSITY_DEPTH = 1.0 / 0xf
DETAIL_MODEL_COUNT_LIMIT = 0x3f
HEADER_SIZE = 24
