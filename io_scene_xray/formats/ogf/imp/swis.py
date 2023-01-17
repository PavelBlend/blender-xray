# addon modules
from .. import fmt
from ... import level
from .... import rw


def import_swi(visual, chunks, ogf_chunks):
    swi = import_swidata(chunks, ogf_chunks)

    if swi:
        visual.indices = visual.indices[swi[0].offset : ]
        visual.indices_count = swi[0].triangles_count * 3


def import_swicontainer(chunks):
    swicontainer_data = chunks.pop(fmt.Chunks_v4.SWICONTAINER)
    packed_reader = rw.read.PackedReader(swicontainer_data)
    swi_index = packed_reader.getf('<I')[0]
    return swi_index


def import_swidata(chunks, ogf_chunks):
    if not hasattr(ogf_chunks, 'SWIDATA'):
        return
    swi_data = chunks.pop(ogf_chunks.SWIDATA)
    packed_reader = rw.read.PackedReader(swi_data)
    swi = level.swi.import_slide_window_item(packed_reader)
    return swi
