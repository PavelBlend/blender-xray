import xray_io
from . import fmt
from . import custom_object
from . import scene_object


def dump_object_count(data):
    packed_reader = xray_io.PackedReader(data)

    count = packed_reader.getf('<I')[0]

    print('            Object Count:', count)


def dump_objects(data):
    chunked_reader = xray_io.ChunkedReader(data)

    for object_id, object_data in chunked_reader.read():
        print('            Object:', object_id)
        _dump_object(object_data)


def dump_object_body(data):
    chunked_reader = xray_io.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader.read():

        # custom object
        if chunk_id == fmt.ObjectChunks.FLAGS:
            print('                    CUSTOM OBJECT FLAGS:')
            custom_object.dump_flags(chunk_data)

        elif chunk_id == fmt.ObjectChunks.TRANSFORM:
            print('                    CUSTOM OBJECT TRANSFORM:')
            custom_object.dump_transform(chunk_data)

        elif chunk_id == fmt.ObjectChunks.NAME:
            print('                    CUSTOM OBJECT NAME:')
            custom_object.dump_name(chunk_data)

        # scene object
        elif chunk_id == fmt.SceneObjectChunks.VERSION:
            print('                    SCENE OBJECT VERSION:')
            scene_object.dump_version(chunk_data)

        elif chunk_id == fmt.SceneObjectChunks.FLAGS:
            print('                    SCENE OBJECT FLAGS:')
            scene_object.dump_flags(chunk_data)

        elif chunk_id == fmt.SceneObjectChunks.REFERENCE:
            print('                    SCENE OBJECT REFERENCE:')
            scene_object.dump_reference(chunk_data)

        # unknown chunks
        else:
            raise BaseException('Unsupported chunk: 0x{:x}'.format(chunk_id))


def _dump_object_class(data):
    packed_reader = xray_io.PackedReader(data)

    object_class = packed_reader.getf('<I')[0]

    if object_class != fmt.ClassID.OBJECT:
        raise BaseException('Unsupported object class: {}'.format(object_class))

    print('                    Object Class:', object_class)


def _dump_object(data):
    chunked_reader = xray_io.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader.read():

        if chunk_id == fmt.CustomObjectChunks.CLASS:
            print('                OBJECT CLASS:')
            _dump_object_class(chunk_data)

        elif chunk_id == fmt.CustomObjectChunks.BODY:
            print('                OBJECT BODY:')
            dump_object_body(chunk_data)

        else:
            raise BaseException('Unsupported chunk: 0x{:x}'.format(chunk_id))
