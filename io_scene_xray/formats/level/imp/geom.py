# standart modules
import os

# addon modules
from . import header
from .. import fmt
from .... import text
from .... import log
from .... import rw


def read_geom(level, chunks, context):
    if level.xrlc_version <= fmt.VERSION_12:
        return

    geom_path = context.filepath + os.extsep + 'geom'

    if os.path.exists(geom_path):
        geom_reader = rw.utils.get_file_reader(
            geom_path,
            chunked=True,
            update_log=False
        )
        geom_chunks = rw.utils.get_reader_chunks(geom_reader)
        header.get_version(geom_chunks, geom_path)
        chunks.update(geom_chunks)

    else:
        raise log.AppError(
            text.error.level_has_no_geom,
            log.props(path=geom_path)
        )
