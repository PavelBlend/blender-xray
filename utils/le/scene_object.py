import xray_io
from . import fmt


def dump_flags(data):
    packed_reader = xray_io.PackedReader(data)

    flags = packed_reader.getf('<I')[0]

    print('                        Flags:', flags)


def dump_version(data):
    packed_reader = xray_io.PackedReader(data)

    version = packed_reader.getf('<H')[0]

    if version != fmt.SCENE_OBJECT_VERSION:
        raise BaseException('unsupported scene object format: {}'.format(version))

    print('                        Version:', version)


def dump_reference(data):
    packed_reader = xray_io.PackedReader(data)

    version = packed_reader.getf('<I')[0]
    reserved = packed_reader.getf('<I')[0]
    reference = packed_reader.gets()

    print('                        Version:', version)
    print('                        Reserved:', reserved)
    print('                        Reference:', reference)
