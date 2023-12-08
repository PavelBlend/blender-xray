# addon modules
from . import fmt
from ... import text
from ... import log
from ... import rw


def _read_object_body_version(chunked_reader):
    # get scene object version
    ver_chunk = chunked_reader.get_chunk(fmt.SceneObjectChunks.VERSION)
    packed_reader = rw.read.PackedReader(ver_chunk)
    ver = packed_reader.getf('<H')[0]

    # check version
    if not ver in (fmt.OBJECT_VER_SOC, fmt.OBJECT_VER_COP):
        raise log.AppError(
            text.error.scene_obj_ver,
            log.props(version=ver)
        )

    return ver


def _read_object_body_data(chunked_reader, ver):
    ref = None
    pos = None
    rot = None
    scl = None

    for chunk_id, chunk_data in chunked_reader:

        # reference
        if chunk_id == fmt.SceneObjectChunks.REFERENCE:
            packed_reader = rw.read.PackedReader(chunk_data)

            if ver == fmt.OBJECT_VER_SOC:
                version = packed_reader.uint32()
                reserved = packed_reader.uint32()

            ref = packed_reader.gets()

        # transforms
        elif chunk_id == fmt.ObjectChunks.TRANSFORM:
            packed_reader = rw.read.PackedReader(chunk_data)

            pos = packed_reader.getf('<3f')
            rot = packed_reader.getf('<3f')
            scl = packed_reader.getf('<3f')

    return ref, pos, rot, scl


def _read_object_body(data):
    chunked_reader = rw.read.ChunkedReader(data)

    # read version
    ver = _read_object_body_version(chunked_reader)

    # read object data
    ref, pos, rot, scl = _read_object_body_data(chunked_reader, ver)

    return ref, pos, rot, scl


def _read_object(data):
    ref = None
    pos = None
    rot = None
    scl = None

    chunked_reader = rw.read.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader:

        if chunk_id == fmt.SceneChunks.LEVEL_TAG:
            ref, pos, rot, scl = _read_object_body(chunk_data)
            break

    return ref, pos, rot, scl


def _read_objects(data):
    references = []
    positions = []
    rotations = []
    scales = []

    chunked_reader = rw.read.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader:
        ref, pos, rot, scl = _read_object(chunk_data)
        references.append(ref)
        positions.append(pos)
        rotations.append(rot)
        scales.append(scl)

    return references, positions, rotations, scales


def read_data(data):
    chunked_reader = rw.read.ChunkedReader(data)
    objs_chunk = chunked_reader.get_chunk(fmt.CustomObjectsChunks.OBJECTS)
    refs, poss, rots, scls = _read_objects(objs_chunk)
    return refs, poss, rots, scls
