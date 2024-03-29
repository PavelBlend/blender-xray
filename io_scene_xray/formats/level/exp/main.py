# standart modules
import os

# addon modules
from . import level
from . import geom
from . import cform
from .... import log
from .... import utils


FILE_NAME = 'level'
GEOM_EXT = 'geom'
GEOMX_EXT = 'geomx'


@log.with_context(name='export-game-level')
@utils.stats.timer
def export_file(context, bpy_obj, dir_path):
    log.update(object=bpy_obj.name)
    file_path = os.path.join(dir_path, FILE_NAME)
    utils.stats.status('Export File', file_path)

    # write level file
    vbs, ibs, fp_vbs, fp_ibs, lvl = level.write_level(context, file_path, bpy_obj)

    # write level.geom file
    geom.write_geom(file_path, vbs, ibs, GEOM_EXT)

    # write level.geomx file
    geom.write_geom(file_path, fp_vbs, fp_ibs, GEOMX_EXT)

    # write level.cform file
    cform.write_cform(file_path, lvl)
