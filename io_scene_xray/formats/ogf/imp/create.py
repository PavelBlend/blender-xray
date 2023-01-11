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


def create_root_visual(context, visual, model_types):
    if visual.model_type in (model_types.NORMAL, model_types.PROGRESSIVE):
        indices.convert_indices_to_triangles(visual)
        bpy_object = mesh.create_visual(visual)

    elif visual.model_type == model_types.HIERRARHY:
        bpy_object = visual.root_obj

    else:
        bpy_object = None

    utility.set_export_path(context, visual, bpy_object)


def create_child_visual(context, visual):
    indices.convert_indices_to_triangles(visual)
    bpy_object = mesh.create_visual(visual)
    arm = visual.arm_obj

    if arm:
        bpy_object.parent = arm
        mod = bpy_object.modifiers.new('Armature', 'ARMATURE')
        mod.object = arm
        bpy_object.xray.isroot = False

    elif visual.root_obj:
        bpy_object.parent = visual.root_obj
        bpy_object.xray.version = context.version
        bpy_object.xray.isroot = False


def import_level_geometry_v4(chunks, visual, lvl):
    chunks_ids = fmt.Chunks_v4

    gcontainer_data = chunks.pop(chunks_ids.GCONTAINER, None)
    if gcontainer_data:
        vb_index, vb_offset, vb_size, ib_index, ib_offset, ib_size = gcontainer.read_gcontainer_v4(gcontainer_data)

    else:
        # vcontainer
        vcontainer_data = chunks.pop(chunks_ids.VCONTAINER)
        vb_index, vb_offset, vb_size = gcontainer.read_container_v3(vcontainer_data)
    
        # icontainer
        icontainer_data = chunks.pop(chunks_ids.ICONTAINER)
        ib_index, ib_offset, ib_size = gcontainer.read_container_v3(icontainer_data)

    fastpath_data = chunks.pop(chunks_ids.FASTPATH, None)    # optional chunk
    if fastpath_data:
        visual.fastpath = True
    else:
        visual.fastpath = False

    bpy_mesh, geometry_key = gcontainer.import_gcontainer(
        visual, lvl,
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

    # vcontainer
    vcontainer_data = chunks.pop(chunks_ids.VCONTAINER, None)
    if vcontainer_data:
        vb_index, vb_offset, vb_size = gcontainer.read_container_v3(vcontainer_data)
    else:
        vertices_data = chunks.pop(chunks_ids.VERTICES)
        verts.read_vertices_v3(vertices_data, visual, lvl)
        vb_index = None
        vb_offset = None
        vb_size = None

    # icontainer
    icontainer_data = chunks.pop(chunks_ids.ICONTAINER, None)
    if icontainer_data:
        ib_index, ib_offset, ib_size = gcontainer.read_container_v3(icontainer_data)
    else:
        indices_data = chunks.pop(chunks_ids.INDICES)
        indices.read_indices_v3(indices_data, visual)
        ib_index = None
        ib_offset = None
        ib_size = None

    bpy_mesh, geometry_key = gcontainer.import_gcontainer(
        visual, lvl,
        vb_index, vb_offset, vb_size,
        ib_index, ib_offset, ib_size
    )
    return bpy_mesh, geometry_key


def import_level_geometry(chunks, visual, lvl):
    if visual.format_version == fmt.FORMAT_VERSION_4:
        bpy_mesh, geometry_key = import_level_geometry_v4(chunks, visual, lvl)

    elif visual.format_version in (fmt.FORMAT_VERSION_3, fmt.FORMAT_VERSION_2):
        bpy_mesh, geometry_key = import_level_geometry_v2_v3(chunks, visual, lvl)

    return bpy_mesh, geometry_key


def create_hierrarhy_obj(context, visual):
    root_obj = bpy.data.objects.new(visual.name, None)
    root_obj.xray.version = context.version
    root_obj.xray.isroot = True
    utils.version.link_object(root_obj)
    visual.root_obj = root_obj
    return root_obj
