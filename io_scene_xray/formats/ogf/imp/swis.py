# addon modules
from .. import fmt
from ... import level
from .... import rw


def import_swi(visual, chunks):
    swi = import_swidata(chunks)
    visual.indices = visual.indices[swi[0].offset : ]
    visual.indices_count = swi[0].triangles_count * 3


def import_swicontainer(chunks):
    swicontainer_data = chunks.pop(fmt.Chunks_v4.SWICONTAINER)
    packed_reader = rw.read.PackedReader(swicontainer_data)
    del swicontainer_data
    swi_index = packed_reader.getf('<I')[0]
    return swi_index


def import_swidata(chunks):
    swi_data = chunks.pop(fmt.Chunks_v4.SWIDATA)
    packed_reader = rw.read.PackedReader(swi_data)
    del swi_data
    swi = level.swi.import_slide_window_item(packed_reader)
    del packed_reader
    return swi
