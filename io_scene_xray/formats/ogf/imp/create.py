# blender modules
import bpy

# addon modules
from . import header
from . import indices
from . import utility
from . import mesh
from . import verts
from . import gcontainer
from .. import fmt
from .... import utils


ROOT_ERROR = 'OGF IMPORT ERROR: cannot find root object!'


def create_root_visual(context, visual, types):
    if visual.model_type in (types.NORMAL, types.PROGRESSIVE):
        indices.convert_indices_to_triangles(visual)
        bpy_object = mesh.create_visual(visual)

    elif visual.model_type == types.HIERRARHY:
        bpy_object = visual.root_obj

    elif visual.model_type in (types.SKELETON_RIGID, types.SKELETON_ANIM):
        bpy_object = visual.arm_obj

    else:
        raise BaseException(ROOT_ERROR)

    utility.set_export_path(context, visual, bpy_object)


def create_child_visual(context, visual):
    indices.convert_indices_to_triangles(visual)
    bpy_object = mesh.create_visual(visual)

    arm = visual.arm_obj
    root = visual.root_obj

    if arm:
        parent = arm
        mod = bpy_object.modifiers.new('Armature', 'ARMATURE')
        mod.object = arm

    elif root:
        parent = root

    else:
        raise BaseException(ROOT_ERROR)

    bpy_object.parent = parent
    bpy_object.xray.version = context.version
    bpy_object.xray.isroot = False


def import_geom_from_container(
        visual, lvl, has_vc, has_ic,
        vb_index, vb_offset, vb_size,
        ib_index, ib_offset, ib_size
    ):

    bpy_mesh = None
    geometry_key = None

    if has_vc and has_ic:
        geometry_key = (
            vb_index, vb_offset, vb_size,
            ib_index, ib_offset, ib_size
        )
        bpy_mesh = lvl.loaded_geometry.get(geometry_key, None)
        if bpy_mesh:
            return bpy_mesh, geometry_key

    if has_vc:
        gcontainer.load_vcontainer(
            visual,
            lvl,
            vb_index,
            vb_offset,
            vb_size
        )

    if has_ic:
        gcontainer.load_icontainer(
            visual,
            lvl,
            ib_index, 
            ib_offset,
            ib_size
        )

    return bpy_mesh, geometry_key


def import_level_geometry_v4(chunks, visual, lvl):
    chunks_ids = fmt.Chunks_v4

    gc_data = chunks.pop(chunks_ids.GCONTAINER, None)

    if gc_data:
        (
            vb_index, vb_offset, vb_size,
            ib_index, ib_offset, ib_size
        ) = gcontainer.read_gcontainer_v4(gc_data)

    else:
        # vcontainer data
        vc_data = chunks.pop(chunks_ids.VCONTAINER)
        vb_index, vb_offset, vb_size = gcontainer.read_container_v3(vc_data)
    
        # icontainer data
        ic_data = chunks.pop(chunks_ids.ICONTAINER)
        ib_index, ib_offset, ib_size = gcontainer.read_container_v3(ic_data)

    fastpath_data = chunks.pop(chunks_ids.FASTPATH, None)    # optional chunk
    if fastpath_data:
        visual.fastpath = True
    else:
        visual.fastpath = False

    bpy_mesh, geometry_key = import_geom_from_container(
        visual, lvl, True, True,
        vb_index, vb_offset, vb_size,
        ib_index, ib_offset, ib_size
    )

    return bpy_mesh, geometry_key


def import_level_geometry_v2_v3(chunks, visual, lvl):
    if visual.format_version == fmt.FORMAT_VERSION_3:
        chunks_ids = fmt.Chunks_v3
    else:
        chunks_ids = fmt.Chunks_v2

    # bbox
    bbox_data = chunks.pop(chunks_ids.BBOX)
    header.read_bbox_v3(bbox_data)

    # bsphere
    bsphere_data = chunks.pop(chunks_ids.BSPHERE)
    header.read_bsphere_v3(bsphere_data)

    has_vc = False
    has_ic = False

    vb_index = None
    vb_offset = None
    vb_size = None

    ib_index = None
    ib_offset = None
    ib_size = None

    # vcontainer data
    vc_data = chunks.pop(chunks_ids.VCONTAINER, None)
    if vc_data:
        vb_index, vb_offset, vb_size = gcontainer.read_container_v3(vc_data)
        has_vc = True
    else:
        vertices_data = chunks.pop(chunks_ids.VERTICES)
        verts.read_vertices_v3(vertices_data, visual, lvl)

    # icontainer data
    ic_data = chunks.pop(chunks_ids.ICONTAINER, None)
    if ic_data:
        ib_index, ib_offset, ib_size = gcontainer.read_container_v3(ic_data)
        has_ic = True
    else:
        indices_data = chunks.pop(chunks_ids.INDICES)
        indices.read_indices_v3(indices_data, visual)

    bpy_mesh, geometry_key = import_geom_from_container(
        visual, lvl, has_vc, has_ic,
        vb_index, vb_offset, vb_size,
        ib_index, ib_offset, ib_size
    )

    return bpy_mesh, geometry_key


def import_level_geometry(chunks, visual, lvl):
    if visual.format_version == fmt.FORMAT_VERSION_4:
        import_fun = import_level_geometry_v4

    elif visual.format_version in (fmt.FORMAT_VERSION_2, fmt.FORMAT_VERSION_3):
        import_fun = import_level_geometry_v2_v3

    bpy_mesh, geometry_key = import_fun(chunks, visual, lvl)

    return bpy_mesh, geometry_key


def create_hierrarhy_obj(context, visual):
    root_obj = bpy.data.objects.new(visual.name, None)
    utils.version.link_object(root_obj)

    root_obj.xray.version = context.version
    root_obj.xray.isroot = True
    
    visual.root_obj = root_obj

    return root_obj
