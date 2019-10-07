import os, time

import bpy, bmesh, mathutils

from .. import xray_io, utils, plugin_prefs
from ..ogf import exp as ogf_exp
from . import fmt, vb


class Visual(object):
    def __init__(self):
        self.shader_index = None


class Level(object):
    def __init__(self):
        self.materials = {}
        self.visuals = []
        self.active_material_index = 0


def write_level_geom_swis():
    packed_writer = xray_io.PackedWriter()

    packed_writer.putf('<I', 0)    # swis count

    return packed_writer


def write_level_geom_ib(ib):
    packed_writer = xray_io.PackedWriter()

    indices_count = len(ib)
    packed_writer.putf('<I', 1)    # indices buffers count
    packed_writer.putf('<I', indices_count)    # indices count

    for index in range(0, indices_count, 3):
        packed_writer.putf('<H', ib[index])
        packed_writer.putf('<H', ib[index + 2])
        packed_writer.putf('<H', ib[index + 1])

    return packed_writer


def write_level_geom_vb(vb):
    packed_writer = xray_io.PackedWriter()

    packed_writer.putf('<I', 1)    # vertex buffers count

    offsets = (0, 12, 16, 20, 24, 28)    # normal visual vertex buffer offsets
    usage_indices = (0, 0, 0, 0, 0, 1)

    for index, (usage, type_) in enumerate(fmt.VERTEX_TYPE_BRUSH):
        packed_writer.putf('<H', 0)    # stream
        packed_writer.putf('<H', offsets[index])    # offset
        packed_writer.putf('<B', type_)    # type
        packed_writer.putf('<B', 0)    # method
        packed_writer.putf('<B', usage)    # usage
        packed_writer.putf('<B', usage_indices[index])    # usage_index

    packed_writer.putf('<H', 255)    # stream
    packed_writer.putf('<H', 0)    # offset
    packed_writer.putf('<B', 17)   # type UNUSED
    packed_writer.putf('<B', 0)    # method
    packed_writer.putf('<B', 0)    # usage
    packed_writer.putf('<B', 0)    # usage_index

    packed_writer.putf('<I', len(vb.position))    # vertices count

    for vertex_index, vertex_pos in enumerate(vb.position):
        packed_writer.putf('3f', *vertex_pos)
        packed_writer.putf(
            '4B',
            vb.normal[vertex_index][0],
            vb.normal[vertex_index][2],
            vb.normal[vertex_index][1],
            31
        )    # normal, hemi
        uv_fix = vb.uv_fix[vertex_index]
        packed_writer.putf('4B', 127, 127, 127, uv_fix[0])    # tangent
        packed_writer.putf('4B', 127, 127, 127, uv_fix[1])    # binormal
        # texture coordinate
        packed_writer.putf(
            '2h', vb.uv[vertex_index][0], vb.uv[vertex_index][1]
        )
        # light map texture coordinate
        packed_writer.putf(
            '2h', vb.uv_lmap[vertex_index][0], vb.uv_lmap[vertex_index][1]
        )

    return packed_writer


def write_level_geom(chunked_writer, vb, ib):
    header_packed_writer = write_header()
    chunked_writer.put(fmt.Chunks.HEADER, header_packed_writer)
    del header_packed_writer

    vb_packed_writer = write_level_geom_vb(vb)
    chunked_writer.put(fmt.Chunks.VB, vb_packed_writer)
    del vb_packed_writer

    ib_packed_writer = write_level_geom_ib(ib)
    chunked_writer.put(fmt.Chunks.IB, ib_packed_writer)
    del ib_packed_writer

    swis_packed_writer = write_level_geom_swis()
    chunked_writer.put(fmt.Chunks.SWIS, swis_packed_writer)
    del swis_packed_writer


def write_sector_root(root_index):
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<I', root_index)
    return packed_writer


def write_sector_portals(sectors_map, sector_index):
    packed_writer = xray_io.PackedWriter()
    # None - when there are no sectors
    if sectors_map.get(sector_index, None):
        for portal in sectors_map[sector_index]:
            packed_writer.putf('<H', portal)
    return packed_writer


def write_sector(root_index, sectors_map, sector_index):
    chunked_writer = xray_io.ChunkedWriter()

    sector_portals_writer = write_sector_portals(sectors_map, sector_index)
    chunked_writer.put(0x1, sector_portals_writer)    # portals

    sector_root_writer = write_sector_root(root_index)
    chunked_writer.put(0x2, sector_root_writer)    # root

    return chunked_writer


def write_shaders(level):
    texture_folder = plugin_prefs.get_preferences().textures_folder_auto
    materials = {}
    max_index = 0
    for material, shader_index in level.materials.items():
        if shader_index > max_index:
            max_index = shader_index
        materials[shader_index] = material
    materials_count = len(materials)
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<I', materials_count + 1)    # shaders count
    packed_writer.puts('')
    for shader_index in range(materials_count):
        material = materials[shader_index]
        texture_node = material.node_tree.nodes['Image Texture']
        texture_path = utils.gen_texture_name(texture_node, texture_folder)
        eshader = material.xray.eshader

        lmap_1_node = material.node_tree.nodes.get('Image Texture.001', None)
        if lmap_1_node:
            lmap_1_path = lmap_1_node.image.name
        else:
            lmap_1_path = 'lmap#1_1'

        lmap_2_node = material.node_tree.nodes.get('Image Texture.002', None)
        if lmap_2_node:
            lmap_2_path = lmap_2_node.image.name
        else:
            lmap_2_path = 'lmap#1_1'

        packed_writer.puts('{0}/{1},{2},{3}'.format(
            eshader, texture_path, lmap_1_path, lmap_2_path
        ))
    return packed_writer


def write_visual_bounding_sphere(packed_writer, bpy_obj, center, radius):
    packed_writer.putf('<3f', center[0], center[2], center[1])    # center
    packed_writer.putf('<f', radius)    # radius


def write_visual_bounding_box(packed_writer, bpy_obj, bbox):
    bbox_min = bbox[0]
    bbox_max = bbox[1]
    packed_writer.putf('<3f', bbox_min[0], bbox_min[2], bbox_min[1])    # min
    packed_writer.putf('<3f', bbox_max[0], bbox_max[2], bbox_max[1])    # max


def write_visual_header(bpy_obj, visual=None, visual_type=0, shader_id=1):
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<B', 4)    # format version
    packed_writer.putf('<B', visual_type)    # model type NORMAL
    if visual:
        packed_writer.putf('<H', visual.shader_index + 1)
    else:
        packed_writer.putf('<H', shader_id)    # shader id
    data = bpy_obj.xray
    if bpy_obj.type == 'MESH':
        bbox, (center, radius) = ogf_exp.calculate_bbox_and_bsphere(
            bpy_obj, apply_transforms=True
        )
    else:
        bbox = (data.bbox_min, data.bbox_max)
        center = data.center
        radius = data.radius
    write_visual_bounding_box(packed_writer, bpy_obj, bbox)
    write_visual_bounding_sphere(packed_writer, bpy_obj, center, radius)
    return packed_writer


def get_tex_coord_correct(tex_coord_f, tex_coord_h, uv_coeff):
    if tex_coord_f > 0:
        tex_coord_diff = tex_coord_f - (tex_coord_h / uv_coeff)
    else:
        tex_coord_diff = (1 + (tex_coord_f * uv_coeff - tex_coord_h)) / uv_coeff
        tex_coord_h -= 1

    tex_correct = (255 * 0x8000 * tex_coord_diff) / 32
    return int(round(tex_correct, 0)), tex_coord_h


def write_gcontainer(bpy_obj, vb, ib, vb_offset, ib_offset, level):
    visual = Visual()
    material = bpy_obj.data.materials[0]
    if level.materials.get(material, None) is None:
        level.materials[material] = level.active_material_index
        visual.shader_index = level.active_material_index
        level.active_material_index += 1
    else:
        visual.shader_index = level.materials[material]

    packed_writer = xray_io.PackedWriter()

    bm = bmesh.new()
    bm.from_mesh(bpy_obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)

    uv_layer = bm.loops.layers.uv['Texture']
    uv_layer_lmap = bm.loops.layers.uv.get('Light Map', None)
    vertex_color_sun = bm.loops.layers.color.get('Sun', None)

    vertices_count = 0
    indices_count = 0
    vertex_index = 0

    unique_verts = {}
    verts_indices = {}
    for face in bm.faces:
        for loop in face.loops:
            vert = loop.vert
            vert_co = (vert.co[0], vert.co[1], vert.co[2])
            normal = (vert.normal[0], vert.normal[1], vert.normal[2])
            uv = loop[uv_layer].uv[0], loop[uv_layer].uv[1]
            if uv_layer_lmap:
                uv_lmap = loop[uv_layer_lmap].uv[0], loop[uv_layer_lmap].uv[1]
            else:
                uv_lmap = (0.0, 0.0)
            if unique_verts.get(vert_co, None):
                if not (uv, uv_lmap, normal) in unique_verts[vert_co]:
                    unique_verts[vert_co].append((uv, uv_lmap, normal))
                    verts_indices[vert_co].append(vertex_index)
                    vertex_index += 1
            else:
                unique_verts[vert_co] = [(uv, uv_lmap, normal), ]
                verts_indices[vert_co] = [vertex_index, ]
                vertex_index += 1

    vertex_index = 0
    saved_verts = set()
    if uv_layer_lmap or vertex_color_sun:
        uv_coeff = fmt.UV_COEFFICIENT
    else:
        uv_coeff = fmt.UV_COEFFICIENT_2
    for face in bm.faces:
        for loop in face.loops:
            vert = loop.vert
            vert_co = (vert.co[0], vert.co[1], vert.co[2])
            vert_data = unique_verts[vert_co]
            uv = loop[uv_layer].uv
            if uv_layer_lmap:
                uv_lmap = loop[uv_layer_lmap].uv
            else:
                uv_lmap = (0.0, 0.0)
            for index, data in enumerate(vert_data):
                if data[0] == (uv[0], uv[1]) and \
                        data[1] == (uv_lmap[0], uv_lmap[1]) and \
                        data[2] == (vert.normal[0], vert.normal[1], vert.normal[2]):
                    tex_uv, tex_uv_lmap, normal = data
                    vert_index = verts_indices[vert_co][index]
                    break
            ib.append(vert_index)
            indices_count += 1
            if not vert_index in saved_verts:
                saved_verts.add(vert_index)
                vertex_index += 1
                vertices_count += 1
                vb.position.append((
                    vert.co[0],
                    vert.co[2],
                    vert.co[1]
                ))
                vb.normal.append((
                    int(round(((normal[0] + 1.0) / 2) * 255, 0)),
                    int(round(((normal[2] + 1.0) / 2) * 255, 0)),
                    int(round(((normal[1] + 1.0) / 2) * 255, 0))
                ))
                # uv
                tex_coord_u = int(tex_uv[0] * uv_coeff)
                tex_coord_v = int((1 - tex_uv[1]) * uv_coeff)
                # uv correct
                tex_coord_u_correct, tex_coord_u = get_tex_coord_correct(tex_uv[0], tex_coord_u, uv_coeff)
                tex_coord_v_correct, tex_coord_v = get_tex_coord_correct(1 - tex_uv[1], tex_coord_v, uv_coeff)
                pw = xray_io.PackedWriter()
                try:
                    pw.putf('<2B', tex_coord_u_correct, tex_coord_v_correct)
                except:
                    raise BaseException('1')
                # set uv limits
                if not (-0x8000 < tex_coord_u < 0x7fff):
                    tex_coord_u = 0x7fff
                if not (-0x8000 < tex_coord_v < 0x7fff):
                    tex_coord_v = 0x7fff
                vb.uv.append((
                    tex_coord_u,
                    tex_coord_v
                ))
                vb.uv_fix.append((
                    tex_coord_u_correct,
                    tex_coord_v_correct
                ))
                vb.uv_lmap.append((
                    int(round(tex_uv_lmap[0] * fmt.LIGHT_MAP_UV_COEFFICIENT, 0)),
                    int(round((1 - tex_uv_lmap[1]) * fmt.LIGHT_MAP_UV_COEFFICIENT, 0))
                ))

    packed_writer.putf('<I', 0)    # vb_index
    packed_writer.putf('<I', vb_offset)    # vb_offset
    packed_writer.putf('<I', vertices_count)    # vb_size

    vb_offset += vertices_count

    packed_writer.putf('<I', 0)    # ib_index
    packed_writer.putf('<I', ib_offset)    # ib_offset
    packed_writer.putf('<I', indices_count)    # ib_size

    ib_offset += indices_count

    return packed_writer, vb_offset, ib_offset, visual


def write_normal_visual(bpy_obj, vb, ib, vb_offset, ib_offset, level):
    gcontainer_writer, vb_offset, ib_offset, visual = write_gcontainer(
        bpy_obj, vb, ib, vb_offset, ib_offset, level
    )
    return gcontainer_writer, vb_offset, ib_offset, visual


def write_model(bpy_obj, vb, ib, vb_offset, ib_offset, level):
    gcontainer_writer, vb_offset, ib_offset, visual = write_normal_visual(
        bpy_obj, vb, ib, vb_offset, ib_offset, level
    )
    return gcontainer_writer, vb_offset, ib_offset, visual


def write_ogf_color(packed_writer):
    packed_writer.putf('<3f', 0.0, 0.0, 0.0)    # rgb
    packed_writer.putf('<f', 0.5)    # hemi
    packed_writer.putf('<f', 0.5)    # sun


def write_tree_def_2(bpy_obj, chunked_writer):
    packed_writer = xray_io.PackedWriter()

    location = mathutils.Vector((
        bpy_obj.location[0],
        bpy_obj.location[2],
        bpy_obj.location[1]
    ))
    location_mat = mathutils.Matrix.Translation(location)

    rotation = mathutils.Euler((
        -bpy_obj.rotation_euler[0],
        -bpy_obj.rotation_euler[2],
        -bpy_obj.rotation_euler[1]
    ), 'ZXY')
    rotation_mat = rotation.to_matrix().to_4x4()

    scale = mathutils.Vector((
        bpy_obj.scale[0],
        bpy_obj.scale[2],
        bpy_obj.scale[1]
    ))
    scale_mat = \
        mathutils.Matrix.Scale(scale[0], 4, (1, 0, 0)) @ \
        mathutils.Matrix.Scale(scale[1], 4, (0, 1, 0)) @ \
        mathutils.Matrix.Scale(scale[2], 4, (0, 0, 1))

    matrix = (location_mat @ rotation_mat @ scale_mat).transposed()
    for i in matrix:
        packed_writer.putf('<4f', *i)
    write_ogf_color(packed_writer)
    write_ogf_color(packed_writer)

    return packed_writer


def write_visual(
        bpy_obj, vb, ib, vb_offset, ib_offset,
        hierrarhy, visuals_ids, level
    ):
    if bpy_obj.name.startswith('hierrarhy'):
        chunked_writer = write_hierrarhy_visual(
            bpy_obj, hierrarhy, visuals_ids
        )
        return chunked_writer, vb_offset, ib_offset
    elif bpy_obj.name.startswith('lod'):
        chunked_writer = write_lod_visual(
            bpy_obj, hierrarhy, visuals_ids, level
        )
        return chunked_writer, vb_offset, ib_offset
    else:
        chunked_writer = xray_io.ChunkedWriter()
        gcontainer_writer, vb_offset, ib_offset, visual = write_model(
            bpy_obj, vb, ib, vb_offset, ib_offset, level
        )
        if bpy_obj.name.startswith('tree_st') or bpy_obj.name.startswith('tree_pm'):
            header_writer = write_visual_header(bpy_obj, visual=visual, visual_type=7)
            tree_def_2_writer = write_tree_def_2(bpy_obj, chunked_writer)
            chunked_writer.put(0x1, header_writer)
            chunked_writer.put(0x15, gcontainer_writer)
            chunked_writer.put(0xc, tree_def_2_writer)
        else:
            header_writer = write_visual_header(bpy_obj, visual=visual)
            chunked_writer.put(0x1, header_writer)
            chunked_writer.put(0x15, gcontainer_writer)
        return chunked_writer, vb_offset, ib_offset


def write_children_l(bpy_obj, hierrarhy, visuals_ids):
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<I', len(hierrarhy[bpy_obj.name]))
    for child_obj in hierrarhy[bpy_obj.name]:
        child_index = visuals_ids[child_obj]
        packed_writer.putf('<I', child_index)
    return packed_writer


def write_hierrarhy_visual(bpy_obj, hierrarhy, visuals_ids):
    visual_writer = xray_io.ChunkedWriter()
    header_writer = write_visual_header(bpy_obj, visual_type=0x1, shader_id=0)
    visual_writer.put(0x1, header_writer)
    children_l_writer = write_children_l(bpy_obj, hierrarhy, visuals_ids)
    visual_writer.put(0xa, children_l_writer)
    return visual_writer


def write_lod_def_2(bpy_obj, hierrarhy, visuals_ids, level):
    packed_writer = xray_io.PackedWriter()
    me = bpy_obj.data
    uv_layer = me.uv_layers['Texture']

    visual = Visual()
    material = bpy_obj.data.materials[0]
    if level.materials.get(material, None) is None:
        level.materials[material] = level.active_material_index
        visual.shader_index = level.active_material_index
        level.active_material_index += 1
    else:
        visual.shader_index = level.materials[material]

    for face_index in range(8):
        face = me.polygons[face_index]
        for vertex_index in range(4):
            vert_index = face.vertices[vertex_index]
            vert = me.vertices[vert_index]
            packed_writer.putf('<3f', vert.co.x, vert.co.z, vert.co.y)
            loop_index = range(face.loop_start, face.loop_start + face.loop_total)[vertex_index]
            uv = uv_layer.data[loop_index].uv
            packed_writer.putf('<2f', uv[0], 1 - uv[1])
            # TODO: export vertex light
            packed_writer.putf('<I', 0xffff)
            packed_writer.putf('<B', 127)
            packed_writer.putf('<3B', 127, 127, 127)
    return packed_writer, visual


def write_lod_visual(bpy_obj, hierrarhy, visuals_ids, level):
    visual_writer = xray_io.ChunkedWriter()

    children_l_writer = write_children_l(bpy_obj, hierrarhy, visuals_ids)
    lod_def_2_writer, visual = write_lod_def_2(
        bpy_obj, hierrarhy, visuals_ids, level
    )
    header_writer = write_visual_header(
        bpy_obj, visual=visual, visual_type=0x6
    )

    visual_writer.put(0x1, header_writer)
    visual_writer.put(0xa, children_l_writer)
    visual_writer.put(0xb, lod_def_2_writer)

    return visual_writer


def write_visual_children(
        chunked_writer, vb, ib, vb_offset,
        ib_offset, visual_index, hierrarhy,
        visuals_ids, visuals, level
    ):

    for visual_obj in visuals:
        visual_chunked_writer, vb_offset, ib_offset = write_visual(
            visual_obj, vb, ib, vb_offset, ib_offset,
            hierrarhy, visuals_ids, level
        )
        if visual_chunked_writer:
            chunked_writer.put(visual_index, visual_chunked_writer)
            visual_index += 1
    return vb_offset, ib_offset, visual_index


def find_hierrarhy(visual_obj, visuals_hierrarhy, visual_index, visuals):
    visuals.append(visual_obj)
    visuals_hierrarhy[visual_obj.name] = []
    children_objs = []
    for child_obj in visual_obj.children:
        children_objs.append(child_obj)
        visual_index += 1
        visuals_hierrarhy[visual_obj.name].append(child_obj)

    for child_child_obj in children_objs:
        visuals_hierrarhy, visual_index = find_hierrarhy(
            child_child_obj, visuals_hierrarhy, visual_index, visuals
        )
    return visuals_hierrarhy, visual_index


def write_visuals(level_object, sectors_map, level):
    chunked_writer = xray_io.ChunkedWriter()
    sectors_chunked_writer = xray_io.ChunkedWriter()
    visuals_collection = bpy.data.collections['Visuals']
    vb_offset = 0
    ib_offset = 0
    vertex_buffer = vb.VertexBuffer()
    ib = []
    visual_index = 0
    sector_id = 0
    visuals_hierrarhy = {}
    visuals = []
    for child_obj in level_object.children:
        if child_obj.name.startswith('sectors'):
            for sector_obj in child_obj.children:
                for visual_obj in sector_obj.children:
                    visuals_hierrarhy, visual_index = find_hierrarhy(
                        visual_obj, visuals_hierrarhy, visual_index, visuals
                    )
                    visual_index += 1
    visuals.reverse()
    visuals_ids = {}
    for visual_index, visual_obj in enumerate(visuals):
        visuals_ids[visual_obj] = visual_index
    visual_index = 0
    for child_obj in level_object.children:
        if child_obj.name.startswith('sectors'):
            for sector_obj in child_obj.children:
                for root_obj in sector_obj.children:
                    # write sector
                    root_index = visuals_ids[root_obj]
                    sector_chunked_writer = write_sector(
                        root_index, sectors_map, sector_id
                    )
                    sectors_chunked_writer.put(sector_id, sector_chunked_writer)
                sector_id += 1

    vb_offset, ib_offset, visual_index = write_visual_children(
        chunked_writer, vertex_buffer, ib,
        vb_offset, ib_offset,
        visual_index, visuals_hierrarhy, visuals_ids, visuals, level
    )
    return (
        chunked_writer, vertex_buffer, ib, visual_index,
        sectors_chunked_writer
    )


def write_glow():
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<3f', 0.0, 0.0, 0.0)    # position
    packed_writer.putf('<f', 1.0)    # radius
    packed_writer.putf('<H', 1)    # shader index
    return packed_writer


def write_light():
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('I', 1)
    packed_writer.putf('I', 3)
    packed_writer.putf('4f', 1, 1, 1, 1)
    packed_writer.putf('4f', 1, 1, 1, 1)
    packed_writer.putf('4f', 1, 1, 1, 1)
    packed_writer.putf('3f', 1, 1, 1)
    packed_writer.putf('3f', 1, 1, 1)
    packed_writer.putf('f', 1)
    packed_writer.putf('f', 1)
    packed_writer.putf('f', 1)
    packed_writer.putf('f', 1)
    packed_writer.putf('f', 1)
    packed_writer.putf('f', 1)
    packed_writer.putf('f', 1)
    return packed_writer


def append_portal(sectors_map, sector_index, portal_index):
    if not sectors_map.get(sector_index, None) is None:
        sectors_map[sector_index].append(portal_index)
    else:
        sectors_map[sector_index] = [portal_index, ]


def write_portals(level_object, sectors_map):
    packed_writer = xray_io.PackedWriter()
    for child_obj in level_object.children:
        if child_obj.name.startswith('portals'):
            for portal_index, portal_obj in enumerate(child_obj.children):
                packed_writer.putf('<H', portal_obj.xray.sector_front)
                packed_writer.putf('<H', portal_obj.xray.sector_back)
                append_portal(
                    sectors_map, portal_obj.xray.sector_front, portal_index
                )
                append_portal(
                    sectors_map, portal_obj.xray.sector_back, portal_index
                )
                for vertex in portal_obj.data.vertices:
                    packed_writer.putf(
                        '<3f', vertex.co.x, vertex.co.z, vertex.co.y
                    )
                vertices_count = len(portal_obj.data.vertices)
                for vertex_index in range(vertices_count, 6):
                    packed_writer.putf('<3f', 0.0, 0.0, 0.0)
                packed_writer.putf('<I', vertices_count)
    return packed_writer


def write_header():
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<H', fmt.VERSION_14)
    packed_writer.putf('<H', 0)    # quality
    return packed_writer


def write_level(chunked_writer, level_object):
    level = Level()

    # header
    header_writer = write_header()
    chunked_writer.put(fmt.Chunks.HEADER, header_writer)
    del header_writer

    # portals
    sectors_map = {}
    portals_writer = write_portals(level_object, sectors_map)
    chunked_writer.put(fmt.Chunks.PORTALS, portals_writer)
    del portals_writer

    # light dynamic
    light_writer = write_light()
    chunked_writer.put(fmt.Chunks.LIGHT_DYNAMIC, light_writer)
    del light_writer

    # glow
    glows_writer = write_glow()
    chunked_writer.put(fmt.Chunks.GLOWS, glows_writer)
    del glows_writer

    # visuals
    (visuals_writer, vb, ib, last_visual_index,
    sectors_chunked_writer) = write_visuals(
        level_object, sectors_map, level
    )
    chunked_writer.put(fmt.Chunks.VISUALS, visuals_writer)
    del visuals_writer

    # shaders
    shaders_writer = write_shaders(level)
    chunked_writer.put(fmt.Chunks.SHADERS, shaders_writer)
    del shaders_writer

    # sectors
    chunked_writer.put(fmt.Chunks.SECTORS, sectors_chunked_writer)
    del sectors_chunked_writer

    return vb, ib


def get_writer():
    chunked_writer = xray_io.ChunkedWriter()
    return chunked_writer


def export_file(level_object, file_path):
    start_time = time.time()

    level_chunked_writer = get_writer()
    vb, ib = write_level(level_chunked_writer, level_object)

    with open(file_path, 'wb') as file:
        file.write(level_chunked_writer.data)
    del level_chunked_writer

    level_geom_chunked_writer = get_writer()
    write_level_geom(level_geom_chunked_writer, vb, ib)

    with open(file_path + os.extsep + 'geom', 'wb') as file:
        file.write(level_geom_chunked_writer.data)
    del level_geom_chunked_writer

    print('total time: {}s'.format(time.time() - start_time))
