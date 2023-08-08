# addon modules
from .... import rw
from .... import log
from .... import text


def read_description(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.S_DESC, None)

    if chunk_data:
        packed_reader = rw.read.PackedReader(chunk_data)

        source_file = packed_reader.gets()

        try:
            build_name = packed_reader.gets()
            build_time = packed_reader.uint32()

            visual.create_name = packed_reader.gets()
            visual.create_time = packed_reader.uint32()

            visual.modif_name = packed_reader.gets()
            visual.modif_time = packed_reader.uint32()

        except rw.read.PackedReader.Errors as err:
            log.warn(
                text.warn.ogf_bad_description,
                error=str(err),
                file=visual.file_path
            )

def read_user_data(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.S_USERDATA, None)

    if chunk_data:
        packed_reader = rw.read.PackedReader(chunk_data)

        visual.user_data = packed_reader.gets(
            onerror=lambda err: log.warn(
                text.warn.object_bad_userdata,
                error=str(err),
                file=visual.file_path
            )
        )


def read_lods(context, chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.S_LODS, None)

    if chunk_data:
        packed_reader = rw.read.PackedReader(chunk_data)

        visual.lod = packed_reader.gets()

        if visual.lod.endswith('\r\n'):
            visual.lod = visual.lod[ : -2]


def _read_motion_refs_soc(data, visual):
    packed_reader = rw.read.PackedReader(data)
    visual.motion_refs = packed_reader.gets().split(',')


def _read_motion_refs_cs_cop(data, visual):
    packed_reader = rw.read.PackedReader(data)

    count = packed_reader.uint32()
    visual.motion_refs = [packed_reader.gets() for index in range(count)]


def read_motion_references(chunks, ogf_chunks, visual):
    data = chunks.pop(ogf_chunks.S_MOTION_REFS_0, None)

    if data:
        # soc
        _read_motion_refs_soc(data, visual)

    else:
        # cs/cop
        data = chunks.pop(ogf_chunks.S_MOTION_REFS_2, None)
        if data:
            _read_motion_refs_cs_cop(data, visual)
