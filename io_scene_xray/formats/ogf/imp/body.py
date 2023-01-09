# addon modules
from . import utility
from . import header
from . import props
from . import create
from . import types
from . import model
from . import bone
from . import ik
from . import shader
from . import verts
from . import indices
from . import swis
from .. import fmt
from ... import omf
from .... import log
from .... import rw
from .... import text


def import_mt_skeleton_rigid(context, chunks, ogf_chunks, visual):
    props.import_description(chunks, ogf_chunks, visual)
    bone.import_bone_names(chunks, ogf_chunks, visual)
    props.import_lods(context, chunks, ogf_chunks, visual)
    ik.import_ik_data(chunks, ogf_chunks, visual)
    import_children(context, chunks, ogf_chunks, visual)


def import_mt_hierrarhy(context, chunks, ogf_chunks, visual):
    create.create_hierrarhy_obj(context, visual)
    props.import_description(chunks, ogf_chunks, visual)
    import_children(context, chunks, ogf_chunks, visual)


def import_mt_skeleton_geom_def_st(context, chunks, ogf_chunks, visual):
    shader.import_texture(context, chunks, ogf_chunks, visual)
    verts.import_skeleton_vertices(chunks, ogf_chunks, visual)
    indices.import_indices(chunks, ogf_chunks, visual)


def import_mt_skeleton_geom_def_pm(context, chunks, ogf_chunks, visual):
    import_mt_skeleton_geom_def_st(context, chunks, ogf_chunks, visual)
    swis.import_swi(visual, chunks)


def import_mt_normal(context, chunks, ogf_chunks, visual):
    shader.import_texture(context, chunks, ogf_chunks, visual)
    verts.import_vertices(chunks, ogf_chunks, visual)
    indices.import_indices(chunks, ogf_chunks, visual)


def import_mt_progressive(context, chunks, ogf_chunks, visual):
    import_mt_normal(context, chunks, ogf_chunks, visual)
    swis.import_swi(visual, chunks)


def import_mt_skeleton_anim(context, chunks, ogf_chunks, visual):
    props.read_motion_references(chunks, ogf_chunks, visual)
    import_mt_skeleton_rigid(context, chunks, ogf_chunks, visual)

    motions_data = chunks.pop(ogf_chunks.S_MOTIONS, None)
    params_data = chunks.pop(ogf_chunks.S_SMPARAMS, None)
    context.bpy_arm_obj = visual.arm_obj

    if params_data and motions_data and context.import_motions:
        motions_params, bone_names = omf.imp.read_params(params_data, context)
        omf.imp.read_motions(motions_data, context, motions_params, bone_names)

    elif params_data:
        omf.imp.read_params(params_data, context)


def set_visual_type(visual, root_visual):
    if visual.model_type == fmt.ModelType_v4.SKELETON_GEOMDEF_PM:
        root_visual.arm_obj.xray.flags_simple = 'pd'

    elif visual.model_type == fmt.ModelType_v4.SKELETON_GEOMDEF_ST:
        root_visual.arm_obj.xray.flags_simple = 'dy'

    elif visual.model_type == fmt.ModelType_v4.PROGRESSIVE:
        root_visual.root_obj.xray.flags_simple = 'pd'

    elif visual.model_type == fmt.ModelType_v4.NORMAL:
        root_visual.root_obj.xray.flags_simple = 'dy'

    else:
        print('WARRNING: Model type = {}'.format(visual.model_type))


def import_children(context, chunks, chunks_ids, root_visual):
    chunk_data = chunks.pop(chunks_ids.CHILDREN, None)
    if not chunk_data:
        return
    chunked_reader = rw.read.ChunkedReader(chunk_data)

    for child_index, child_data in chunked_reader:
        visual = types.Visual()
        visual.file_path = root_visual.file_path
        visual.name = root_visual.name + ' {:0>2}'.format(child_index)
        visual.visual_id = child_index
        visual.is_root = False
        visual.arm_obj = root_visual.arm_obj
        visual.root_obj = root_visual.root_obj
        visual.bones = root_visual.bones
        visual.bpy_materials = root_visual.bpy_materials

        import_ogf_visual(context, child_data, visual)
        set_visual_type(visual, root_visual)


def import_ogf_visual(context, data, visual):
    # visual from *.ogf file

    chunks = utility.get_ogf_chunks(data)

    header.read_ogf_file_header(chunks, visual)

    ogf_chunks = fmt.Chunks_v4
    model_types = fmt.ModelType_v4
    props.import_user_data(chunks, ogf_chunks, visual)

    if visual.model_type == model_types.SKELETON_RIGID:
        import_fun = import_mt_skeleton_rigid

    elif visual.model_type == model_types.SKELETON_ANIM:
        import_fun = import_mt_skeleton_anim

    elif visual.model_type == model_types.SKELETON_GEOMDEF_ST:
        import_fun = import_mt_skeleton_geom_def_st

    elif visual.model_type == model_types.SKELETON_GEOMDEF_PM:
        import_fun = import_mt_skeleton_geom_def_pm

    elif visual.model_type == model_types.NORMAL:
        import_fun = import_mt_normal

    elif visual.model_type == model_types.PROGRESSIVE:
        import_fun = import_mt_progressive

    elif visual.model_type == model_types.HIERRARHY:
        import_fun = import_mt_hierrarhy

    else:
        raise log.AppError(
            text.error.ogf_bad_model_type,
            log.props(model_type=visual.model_type)
        )

    import_fun(context, chunks, ogf_chunks, visual)

    utility.check_unread_chunks(chunks)

    if visual.is_root:
        create.create_root_visual(context, visual, model_types)

    else:
        create.create_child_visual(context, visual)


def import_level_visual(data, visual_id, lvl, chunks, visuals_ids):
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
