# addon modules
from .... import rw
from .... import log
from .... import text


def read_description(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.S_DESC)
    packed_reader = rw.read.PackedReader(chunk_data)

    source_file = packed_reader.gets()

    build_name = packed_reader.gets()
    build_time = packed_reader.getf('<I')[0]

    visual.create_name = packed_reader.gets()
    visual.create_time = packed_reader.getf('<I')[0]

    visual.modif_name = packed_reader.gets()
    visual.modif_time = packed_reader.getf('<I')[0]


def import_user_data(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.S_USERDATA, None)
    if not chunk_data:
        return
    packed_reader = rw.read.PackedReader(chunk_data)
    visual.user_data = packed_reader.gets(
        onerror=lambda e: log.warn(
            text.warn.object_bad_userdata,
            error=str(e),
            file=visual.file_path
        )
    )


def read_lods(context, chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.S_LODS, None)
    if not chunk_data:
        return
    packed_reader = rw.read.PackedReader(chunk_data)
    lod = packed_reader.gets()
    if lod.endswith('\r\n'):
        lod = lod[ : -2]
    visual.lod = lod


def read_motion_refs_0(data, visual):
    packed_reader = rw.read.PackedReader(data)
    visual.motion_refs = packed_reader.gets().split(',')


def read_motion_refs_2(data, visual):
    packed_reader = rw.read.PackedReader(data)
    count = packed_reader.getf('<I')[0]
    refs = []
    for index in range(count):
        ref = packed_reader.gets()
        refs.append(ref)
    visual.motion_refs = refs


def read_motion_references(chunks, ogf_chunks, visual):
    data = chunks.pop(ogf_chunks.S_MOTION_REFS_0, None)

    if data:
        read_motion_refs_0(data, visual)

    else:
        data = chunks.pop(ogf_chunks.S_MOTION_REFS_2, None)
        if data:
            read_motion_refs_2(data, visual)
