# standart modules
import os

# addon modules
from .. import le
from ... import log
from ... import text
from ... import utils
from ... import rw


def _read_cs_cop_objects(ltx):
    refs = []
    pos = []
    rot = []
    scl = []

    for section_name, section in ltx.sections.items():
        if not section_name.lower().startswith('object_'):
            continue

        params = section.params
        ref = params.get('reference_name', None)

        if not ref:
            continue

        refs.append(ref)

        obj_name = params.get('name', None)
        position = params.get('position', None)
        rotation = params.get('rotation', None)
        scale = params.get('scale', None)

        for elem, array in zip((position, rotation, scale), (pos, rot, scl)):
            if elem:
                array.append(list(map(float, elem.split(','))))
            else:
                array.append(None)

    return refs, pos, rot, scl


@log.with_context(name='import-part')
@utils.stats.timer
def import_file(file_path, context):
    utils.stats.status('Import File', file_path)

    level_name = os.path.basename(os.path.dirname(file_path))
    file_data = rw.utils.get_file_data(file_path)

    try:
        ltx_data = file_data.decode(encoding='cp1251')
        ltx = rw.ltx.LtxParser()
        ltx.from_str(ltx_data)
    except:
        ltx = None

    if ltx:
        refs, pos, rot, scl = _read_cs_cop_objects(ltx)

    else:
        chunks = rw.utils.get_chunks(file_data)
        data_chunk_id = le.fmt.ToolsChunks.DATA + le.fmt.ClassID.OBJECT
        data_chunk = chunks.get(data_chunk_id, None)

        if data_chunk:
            refs, pos, rot, scl = le.read.read_data(data_chunk)
        else:
            raise log.AppError(text.error.part_no_objs)

    # import
    name = os.path.basename(os.path.dirname(file_path))
    le.imp.import_objects(name, context, refs, pos, rot, scl)
