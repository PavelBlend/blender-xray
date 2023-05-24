# addon modules
from . import main
from . import header
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
from .. import fmt
from .... import utils


def import_hierrarhy_visual(chunks, chunks_fmt, visual, lvl):
    # children link
    children_l_data = chunks.pop(chunks_fmt.CHILDREN_L)
    child.import_children_l(children_l_data, visual, lvl, 'HIERRARHY')

    visual.name = 'hierrarhy'
    bpy_object = utils.obj.create_object(visual.name, None)

    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'HIERRARHY'

    utility.check_unread_chunks(chunks, context='HIERRARHY_VISUAL')

    return bpy_object


def import_render_visual(chunks, visual, lvl, visual_type, chunks_ogf):
    bpy_mesh, geometry_key = create.import_level_geometry(chunks, visual, lvl)
    visual.name = visual_type.lower()

    if bpy_mesh:
        bpy_object = utils.obj.create_object(visual.name, bpy_mesh)

    else:
        if visual_type == 'PROGRESSIVE':
            swi = swis.import_swidata(visual, chunks, chunks_ogf)

            visual.indices = visual.indices[swi[0].offset : ]
            visual.indices_count = swi[0].triangles_count * 3

        indices.convert_indices_to_triangles(visual)

        bpy_object = mesh.create_visual(visual, lvl, geometry_key)

    bpy_object.xray.is_level = True
    bpy_object.xray.level.use_fastpath = visual.fastpath
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = visual_type

    utility.check_unread_chunks(chunks, context=visual_type + '_VISUAL')

    return bpy_object


def import_progressive_visual(chunks, visual, lvl, chunks_ogf):
    bpy_object = import_render_visual(chunks, visual, lvl, 'PROGRESSIVE', chunks_ogf)
    return bpy_object


def import_normal_visual(chunks, visual, lvl, chunks_ogf):
    bpy_object = import_render_visual(chunks, visual, lvl, 'NORMAL', chunks_ogf)
    return bpy_object


def read_mt_skeleton_rigid(context, chunks, ogf_chunks, visual):
    props.read_description(chunks, ogf_chunks, visual)
    props.read_lods(context, chunks, ogf_chunks, visual)
    bone.read_bone_names(chunks, ogf_chunks, visual)
    ik.import_ik_data(chunks, ogf_chunks, visual)
    main.import_children(context, chunks, ogf_chunks, visual)


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
    main.import_children(context, chunks, ogf_chunks, visual)


def read_mt_progressive(context, chunks, ogf_chunks, visual):
    read_mt_normal(context, chunks, ogf_chunks, visual)
    swis.import_swi(visual, chunks, ogf_chunks)


def read_mt_normal(context, chunks, ogf_chunks, visual):
    shader.read_texture(context, chunks, ogf_chunks, visual)
    verts.read_vertices(chunks, ogf_chunks, visual)
    indices.read_indices(chunks, ogf_chunks, visual)
