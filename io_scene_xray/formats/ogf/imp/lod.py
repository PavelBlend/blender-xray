# blender modules
import bpy

# addon modules
from . import utility
from . import header
from . import child
from . import material
from .. import fmt
from ... import level
from .... import rw
from .... import utils


def import_lod_def_2(lvl, data):
    packed_reader = rw.read.PackedReader(data)

    verts = []
    uvs = []
    faces = []
    lights = {'rgb': [], 'hemi': [], 'sun': []}

    if lvl.xrlc_version >= level.fmt.VERSION_11:
        for face_index in range(8):
            face = []

            for vert_index in range(4):
                # reading
                coord_x, coord_y, coord_z = packed_reader.getf('<3f')
                coord_u, coord_v = packed_reader.getf('<2f')
                rgb_hemi = packed_reader.uint32()
                sun = packed_reader.getf('<B')[0]
                packed_reader.skip(3)    # pad (unused)

                # collect geometry
                verts.append((coord_x, coord_z, coord_y))
                face.append(face_index * 4 + vert_index)
                uvs.append((coord_u, 1 - coord_v))

                # collect vertex light
                red, green, blue, hemi = utility.get_float_rgb_hemi(rgb_hemi)

                lights['rgb'].append((red, green, blue, 1.0))
                lights['hemi'].append(hemi)
                lights['sun'].append(sun / 0xff)

            faces.append(face)

    else:
        for face_index in range(8):
            face = []

            for vert_index in range(4):
                # reading
                coord_x, coord_y, coord_z = packed_reader.getf('<3f')
                coord_u, coord_v = packed_reader.getf('<2f')
                light = packed_reader.uint32()

                # collect geometry
                verts.append((coord_x, coord_z, coord_y))
                face.append(face_index * 4 + vert_index)
                uvs.append((coord_u, 1 - coord_v))

                # collect vertex light
                red, green, blue, hemi = utility.get_float_rgb_hemi(light)

                lights['rgb'].append((red, green, blue, 1.0))
                lights['hemi'].append(1.0)
                lights['sun'].append(1.0)

            faces.append(face)

    return verts, uvs, lights, faces


def create_lod_mesh(visual, verts, faces):
    bpy_mesh = bpy.data.meshes.new(visual.name)
    bpy_mesh.from_pydata(verts, (), faces)
    return bpy_mesh


def create_lod_object(obj_name, bpy_mesh, level):
    bpy_obj = utils.obj.create_object(obj_name, bpy_mesh)

    xray = bpy_obj.xray
    xray.version = level.addon_version
    xray.isroot = False
    xray.is_level = True
    xray.level.object_type = 'VISUAL'
    xray.level.visual_type = 'LOD'

    return bpy_obj


def create_lod_layers(bpy_mesh):
    # create uv layer
    if utils.version.IS_28:
        uv_layer = bpy_mesh.uv_layers.new(name='Texture')
    else:
        uv_texture = bpy_mesh.uv_textures.new(name='Texture')
        uv_layer = bpy_mesh.uv_layers[uv_texture.name]

    # create vertex color layers
    rgb_color = bpy_mesh.vertex_colors.new(name='Light')
    hemi_color = bpy_mesh.vertex_colors.new(name='Hemi')
    sun_color = bpy_mesh.vertex_colors.new(name='Sun')

    return uv_layer, rgb_color, hemi_color, sun_color


def assign_lod_layers_values(
        bpy_mesh,
        uvs,
        lights,
        uv_layer,
        rgb_color,
        hemi_color,
        sun_color
    ):
    if utils.version.IS_28:
        for face in bpy_mesh.polygons:
            for loop_index in face.loop_indices:
                loop = bpy_mesh.loops[loop_index]
                vert_index = loop.vertex_index

                # get values
                hemi = lights['hemi'][vert_index]
                sun = lights['sun'][vert_index]

                # set values
                uv_layer.data[loop.index].uv = uvs[vert_index]
                rgb_color.data[loop.index].color = lights['rgb'][vert_index]
                hemi_color.data[loop.index].color = (hemi, hemi, hemi, 1.0)
                sun_color.data[loop.index].color = (sun, sun, sun, 1.0)

    else:
        for face in bpy_mesh.polygons:
            for loop_index in face.loop_indices:
                loop = bpy_mesh.loops[loop_index]
                vert_index = loop.vertex_index

                # get values
                rgb = lights['rgb'][vert_index]
                hemi = lights['hemi'][vert_index]
                sun = lights['sun'][vert_index]

                # set values
                uv_layer.data[loop.index].uv = uvs[vert_index]
                rgb_color.data[loop.index].color = rgb[0 : 3]
                hemi_color.data[loop.index].color = (hemi, hemi, hemi)
                sun_color.data[loop.index].color = (sun, sun, sun)


def import_lod_visual(chunks, visual, lvl):
    if visual.format_version == fmt.FORMAT_VERSION_4:
        chunks_ids = fmt.Chunks_v4

    elif visual.format_version == fmt.FORMAT_VERSION_3:
        chunks_ids = fmt.Chunks_v3

        # bbox
        bbox_data = chunks.pop(chunks_ids.BBOX)
        header.read_bbox_v3(bbox_data)

        # bsphere
        bsphere_data = chunks.pop(chunks_ids.BSPHERE)
        header.read_bsphere_v3(bsphere_data)

    # read chunks

    visual.name = 'lod'

    # children
    children_l_data = chunks.pop(chunks_ids.CHILDREN_L)
    child.import_children_l(children_l_data, visual, lvl, 'LOD')

    # lod def
    lod_def_2_data = chunks.pop(chunks_ids.LODDEF2)
    verts, uvs, lights, faces = import_lod_def_2(lvl, lod_def_2_data)

    utility.check_unread_chunks(chunks, context='LOD_VISUAL')

    # create mesh and object

    bpy_mesh = create_lod_mesh(visual, verts, faces)
    uv_layer, rgb_color, hemi_color, sun_color = create_lod_layers(bpy_mesh)

    assign_lod_layers_values(
        bpy_mesh,
        uvs,
        lights,
        uv_layer,
        rgb_color,
        hemi_color,
        sun_color
    )

    bpy_object = create_lod_object(visual.name, bpy_mesh, lvl)
    material.assign_level_material(bpy_mesh, visual, lvl)

    return bpy_object
