import xray_io
from . import fmt


def dump_flags(data):
    packed_reader = xray_io.PackedReader(data)

    flags = packed_reader.getf('<I')[0]

    print('                        Flags:', flags)

    print('                            Selected:', bool(flags&fmt.CustomObjectFlags.SELECTED))
    print('                            Visible:', bool(flags&fmt.CustomObjectFlags.VISIBLE))
    print('                            Locked:', bool(flags&fmt.CustomObjectFlags.LOCKED))
    print('                            Motion:', bool(flags&fmt.CustomObjectFlags.MOTION))
    print('                            Auto Key:', bool(flags&fmt.CustomObjectFlags.AUTO_KEY))
    print('                            Camera View:', bool(flags&fmt.CustomObjectFlags.CAMERA_VIEW))


def dump_transform(data):
    packed_reader = xray_io.PackedReader(data)

    position = packed_reader.getf('<3f')
    rotation = packed_reader.getf('<3f')
    scale = packed_reader.getf('<3f')

    print('                        Position: {:.3f}, {:.3f}, {:.3f}'.format(*position))
    print('                        Rotation: {:.3f}, {:.3f}, {:.3f}'.format(*rotation))
    print('                        Scale: {:.3f}, {:.3f}, {:.3f}'.format(*scale))


def dump_name(data):
    packed_reader = xray_io.PackedReader(data)

    name = packed_reader.gets()

    print('                        Name:', name)
