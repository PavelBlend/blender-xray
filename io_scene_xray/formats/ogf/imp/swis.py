# addon modules
from .. import fmt
from ... import level
from .... import rw
from .... import log


def import_swicontainer(chunks):
    swicontainer_data = chunks.pop(fmt.Chunks_v4.SWICONTAINER)
    packed_reader = rw.read.PackedReader(swicontainer_data)
    swi_index = packed_reader.uint32()
    return swi_index


def import_swidata_v3(visual, data):
    chunked_reader = rw.read.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader:
        reader = rw.read.PackedReader(chunk_data)

        if chunk_id == fmt.ChunksSwi_v3.HEADER:
            verts_min_count, indices_current = reader.getf('<2I')

        elif chunk_id == fmt.ChunksSwi_v3.VSPLIT:
            vsplit_count = len(chunk_data) // fmt.VSPLIT_SIZE
            vsplit = [
                reader.getf('<H2B')    # vert, new_faces, fix_faces
                for vsplit_index in range(vsplit_count)
            ]

        elif chunk_id == fmt.ChunksSwi_v3.FACES:
            faces_count = reader.getf('<I')[0]
            faces_affected = reader.getf('<{}H'.format(faces_count))

        else:
            log.debug('unknown swidata chunk', chunk_id=chunk_id)

    fix_current = 0
    verts_current = verts_min_count
    verts_count = len(visual.vertices)
    visual.indices = list(visual.indices)

    while verts_current < verts_count:
        vert, new_faces, fix_faces = vsplit[verts_current - verts_min_count]

        for i in range(fix_current, fix_current+fix_faces):
            visual.indices[faces_affected[i]] = verts_current

        verts_current += 1
        fix_current += fix_faces


def import_swi(visual, chunks, ogf_chunks):
    if not hasattr(ogf_chunks, 'SWIDATA'):
        return

    swi_data = chunks.pop(ogf_chunks.SWIDATA)

    if visual.format_version == fmt.FORMAT_VERSION_4:
        packed_reader = rw.read.PackedReader(swi_data)
        swi = level.imp.swi.import_slide_window_item(packed_reader)

        if swi:
            visual.indices = visual.indices[swi[0].offset : ]
            visual.indices_count = swi[0].triangles_count * 3

    elif visual.format_version == fmt.FORMAT_VERSION_3:
        import_swidata_v3(visual, swi_data)
