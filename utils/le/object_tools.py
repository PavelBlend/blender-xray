import xray_io
from . import fmt


def dump_version(data):
    packed_reader = xray_io.PackedReader(data)

    version = packed_reader.getf('<H')[0]

    if version != fmt.OBJECT_TOOLS_VERSION:
        raise BaseException('Unsupported object tools version: {}!'.format(version))

    print('            Object Tools Version:', version)


def dump_flags(data):
    packed_reader = xray_io.PackedReader(data)

    flags = packed_reader.getf('<I')[0]

    print('            Object Tools Flags:', flags)

    print('                Update Props:', bool(flags&fmt.AppendRandomFlags.UpdateProps))
    print('                Scale Proportional:', bool(flags&fmt.AppendRandomFlags.ScaleProportional))
    print('                Append Random:', bool(flags&fmt.AppendRandomFlags.AppendRandom))
    print('                Random Scale:', bool(flags&fmt.AppendRandomFlags.RandomScale))
    print('                Random Rotation:', bool(flags&fmt.AppendRandomFlags.RandomRotation))


def dump_append_random(data):
    packed_reader = xray_io.PackedReader(data)

    min_scale = packed_reader.getf('<3f')
    max_scale = packed_reader.getf('<3f')

    print('            Min Scale: {:.3f}, {:.3f}, {:.3f}'.format(*min_scale))
    print('            Max Scale: {:.3f}, {:.3f}, {:.3f}'.format(*max_scale))

    min_rotation = packed_reader.getf('<3f')
    max_rotation = packed_reader.getf('<3f')

    print('            Min Rotation: {:.3f}, {:.3f}, {:.3f}'.format(*min_rotation))
    print('            Max Rotation: {:.3f}, {:.3f}, {:.3f}'.format(*max_rotation))

    object_count = packed_reader.getf('<I')[0]

    print('            Object Count:', object_count)

    if object_count:
        for _ in range(object_count):
            object_name = packed_reader.gets()
            print('                Object Name:', object_name)
