import time

import xray_io


def dump_guid(data):
    packed_reader = xray_io.PackedReader(data)

    guid_0, guid_1 = packed_reader.getf('<2Q')

    print('        GUID_0, GUID_1:', guid_0, guid_1)


def dump_level_tag(data):
    packed_reader = xray_io.PackedReader(data)

    owner_name = packed_reader.gets()
    create_time = packed_reader.getf('<I')[0]

    time_fmt = '%Y.%m.%d %H:%M'
    create_time_str = time.strftime(time_fmt, time.localtime(create_time))

    print('            Owner Name:', owner_name)
    print('            Create Time:', create_time_str)
