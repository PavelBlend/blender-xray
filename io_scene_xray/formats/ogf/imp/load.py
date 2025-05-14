# addon modules
from . import child
from . import create
from . import indices
from . import mesh
from . import bone
from . import ik
from . import shader
from . import verts
from . import props
from . import utility
from . import motion
from . import swis
from .... import utils


def import_hierrarhy_visual(chunks, chunks_fmt, visual, lvl):
    # children link
    children_l_data = chunks.pop(chunks_fmt.CHILDREN_L)
    child.import_children_l(children_l_data, visual, lvl, 'HIERRARHY')

    visual.name = 'hierrarhy'
    obj = utils.obj.create_object(visual.name, None)

    obj.xray.is_level = True
    obj.xray.level.object_type = 'VISUAL'
    obj.xray.level.visual_type = 'HIERRARHY'

    utility.check_unread_chunks(chunks, context='HIERRARHY_VISUAL')

    return obj


def import_render_visual(chunks, visual, lvl, visual_type, chunks_ogf):
    bpy_mesh, geometry_key = create.import_level_geometry(chunks, visual, lvl)
    visual.name = visual_type.lower()

    if bpy_mesh:
        obj = utils.obj.create_object(visual.name, bpy_mesh)

    else:
        if visual_type == 'PROGRESSIVE':
            swis.import_swi(visual, chunks, chunks_ogf)

        indices.convert_indices_to_triangles(visual)

        obj = mesh.create_visual(visual, lvl, geometry_key)

    obj.xray.is_level = True
    obj.xray.level.use_fastpath = visual.fastpath
    obj.xray.level.object_type = 'VISUAL'
    obj.xray.level.visual_type = visual_type

    utility.check_unread_chunks(chunks, context=visual_type + '_VISUAL')

    return obj


def import_progressive_visual(chunks, visual, lvl, chunks_ogf):
    obj = import_render_visual(chunks, visual, lvl, 'PROGRESSIVE', chunks_ogf)
    return obj


def import_normal_visual(chunks, visual, lvl, chunks_ogf):
    obj = import_render_visual(chunks, visual, lvl, 'NORMAL', chunks_ogf)
    return obj


def read_mt_skeleton_rigid(context, chunks, ogf_chunks, visual):
    props.read_description(chunks, ogf_chunks, visual)
    props.read_lods(context, chunks, ogf_chunks, visual)
    bone.read_bone_names(chunks, ogf_chunks, visual)
    ik.import_ik_data(context, chunks, ogf_chunks, visual)
    child.import_children(context, chunks, ogf_chunks, visual)


def read_mt_skeleton_anim(context, chunks, ogf_chunks, visual):
    props.read_motion_references(chunks, ogf_chunks, visual)
    read_mt_skeleton_rigid(context, chunks, ogf_chunks, visual)
    motion.import_skeleton_motions(context, chunks, ogf_chunks, visual)


def read_mt_skeleton_geom_def_st(context, chunks, ogf_chunks, visual):
    shader.read_texture(context, chunks, ogf_chunks, visual)
    verts.read_skeleton_vertices(chunks, ogf_chunks, visual)
    indices.read_indices(chunks, ogf_chunks, visual)


def read_mt_skeleton_geom_def_pm(context, chunks, ogf_chunks, visual):
    read_mt_skeleton_geom_def_st(context, chunks, ogf_chunks, visual)
    swis.import_swi(visual, chunks, ogf_chunks)


def read_mt_hierrarhy(context, chunks, ogf_chunks, visual):
    create.create_hierrarhy_obj(context, visual)
    props.read_description(chunks, ogf_chunks, visual)
    child.import_children(context, chunks, ogf_chunks, visual)


def read_mt_progressive(context, chunks, ogf_chunks, visual):
    read_mt_normal(context, chunks, ogf_chunks, visual)
    swis.import_swi(visual, chunks, ogf_chunks)


def read_mt_normal(context, chunks, ogf_chunks, visual):
    shader.read_texture(context, chunks, ogf_chunks, visual)
    verts.read_vertices(chunks, ogf_chunks, visual)
    indices.read_indices(chunks, ogf_chunks, visual)
