# standart modules
import os

# addon modules
from . import utility
from . import header
from . import props
from . import create
from . import types
from . import model
from . import load
from .. import fmt
from .... import log
from .... import utils
from .... import rw
from .... import text


def import_ogf_visual(context, data, visual):
    # visual from *.ogf file

    chunks = utility.get_ogf_chunks(data)

    header.read_ogf_file_header(chunks, visual)

    if visual.format_version == fmt.FORMAT_VERSION_4:
        ogf_chunks = fmt.Chunks_v4
        model_types = fmt.ModelType_v4
    elif visual.format_version == fmt.FORMAT_VERSION_3:
        ogf_chunks = fmt.Chunks_v3
        model_types = fmt.ModelType_v3

    if visual.model_type == model_types.SKELETON_RIGID:
        import_fun = load.read_mt_skeleton_rigid

    elif visual.model_type == model_types.SKELETON_ANIM:
        import_fun = load.read_mt_skeleton_anim

    elif visual.model_type == model_types.SKELETON_GEOMDEF_ST:
        import_fun = load.read_mt_skeleton_geom_def_st

    elif visual.model_type == model_types.SKELETON_GEOMDEF_PM:
        import_fun = load.read_mt_skeleton_geom_def_pm

    elif visual.model_type == model_types.NORMAL:
        import_fun = load.read_mt_normal

    elif visual.model_type == model_types.PROGRESSIVE:
        import_fun = load.read_mt_progressive

    elif visual.model_type == model_types.HIERRARHY:
        import_fun = load.read_mt_hierrarhy

    else:
        raise log.AppError(
            text.error.ogf_bad_model_type,
            log.props(model_type=visual.model_type)
        )

    props.read_user_data(chunks, ogf_chunks, visual)
    import_fun(context, chunks, ogf_chunks, visual)

    if visual.arm_obj and not visual.arm_obj.pose.bone_groups:
        props.import_bone_parts(context, visual)

    utility.check_unread_chunks(chunks)

    if visual.is_root:
        create.create_root_visual(context, visual, model_types)

    else:
        create.create_child_visual(context, visual)


def import_level_visual(data, visual_id, lvl):
    # visual from game level file

    chunks = utility.get_ogf_chunks(data)
    visual = types.Visual()
    visual.visual_id = visual_id

    header.read_ogf_level_header(chunks, visual)

    # version 4
    if visual.format_version == fmt.FORMAT_VERSION_4:
        import_function = model.import_model_v4
        chunks_names = fmt.chunks_names_v4
        model_type_names = fmt.model_type_names_v4

    # version 3
    elif visual.format_version == fmt.FORMAT_VERSION_3:
        import_function = model.import_model_v3
        chunks_names = fmt.chunks_names_v3
        model_type_names = fmt.model_type_names_v3

    # version 2
    elif visual.format_version == fmt.FORMAT_VERSION_2:
        import_function = model.import_model_v2
        chunks_names = fmt.chunks_names_v2
        model_type_names = fmt.model_type_names_v2

    import_function(chunks, visual, lvl)


@log.with_context(name='import-ogf')
@utils.stats.timer
def import_file(file_path, context):
    utils.stats.status('Import File', file_path)

    data = rw.utils.get_file_data(file_path)
    file_name = os.path.basename(file_path)

    # init visual
    visual = types.Visual()
    visual.file_path = file_path
    visual.visual_id = 0
    visual.name = file_name
    visual.is_root = True

    import_ogf_visual(context, data, visual)
