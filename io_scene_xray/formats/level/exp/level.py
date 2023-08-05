# standart modules
import os

# addon modules
from . import header
from . import shader
from . import visual
from . import portal
from . import light
from . import glow
from . import types
from .. import fmt
from .... import utils
from .... import rw


def write_level(context, file_path, bpy_obj):
    level = types.Level()
    level.name = os.path.dirname(os.path.basename(file_path))

    level_path = bpy_obj.name
    levels_folders = utils.ie.get_pref_paths('levels_folder')
    for lvls_folder in levels_folders:
        if lvls_folder:
            level_path = os.path.join(lvls_folder, bpy_obj.name)
            break

    level.source_level_path = level_path

    level_writer = rw.write.ChunkedWriter()

    context.level_name = level.name
    level.context = context

    # header
    header.write_header(level_writer)

    # visuals
    (
        vbs,    # vertex buffers for level.geom
        ibs,    # index buffers for level.geom
        vbs_fp,    # fast path vertex buffers for level.geomx
        ibs_fp,    # fast path index buffers for level.geomx
        sectors_writer
    ) = visual.write_visuals(level_writer, bpy_obj, level)

    # portals
    portal.write_portals(level_writer, level, bpy_obj)

    # lights
    light.write_lights(level_writer, level, bpy_obj)

    # glows
    glow.write_glows(level_writer, bpy_obj, level)

    # shaders
    shader.write_shaders(level_writer, level)

    # sectors
    level_writer.put(fmt.Chunks13.SECTORS, sectors_writer)

    # save level file
    rw.utils.save_file(file_path, level_writer)

    return vbs, ibs, vbs_fp, ibs_fp, level
