import os, time, math, struct

import bpy, bmesh, mathutils

from .. import xray_io, utils, plugin_prefs
from ..ogf import exp as ogf_exp, fmt as ogf_fmt
from . import fmt


class VertexBuffer(object):
    def __init__(self):
        self.vertex_count = 0
        self.position = bytearray()
        self.normal = bytearray()
        self.tangent = bytearray()
        self.binormal = bytearray()
        self.color_hemi = bytearray()
        self.color_light = bytearray()
        self.color_sun = bytearray()
        self.uv = bytearray()
        self.uv_fix = bytearray()
        self.uv_lmap = bytearray()
        self.shader_data = bytearray()
        self.vertex_format = None


TWO_MEGABYTES = 1024 * 1024 * 2


class Visual(object):
    def __init__(self):
        self.shader_index = None


class Level(object):
    def __init__(self):
        self.materials = {}
        self.visuals = []
        self.active_material_index = 0
        self.vbs_offsets = []
        self.ibs_offsets = []
        self.fp_vbs_offsets = []
        self.fp_ibs_offsets = []
        self.saved_visuals = {}
        self.sectors_indices = {}
        self.visuals_bbox = {}
        self.visuals_center = {}
        self.visuals_radius = {}
        self.bbox_cache = {}
        self.cform_objects = {}


def write_level_geom_swis():
    packed_writer = xray_io.PackedWriter()

    # TODO: export swis data
    packed_writer.putf('<I', 0)    # swis count

    return packed_writer


def write_level_geom_ib(ibs):
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<I', len(ibs))    # indices buffers count

    for ib in ibs:
        indices_count = len(ib) // 2    # index size = 2 byte
        packed_writer.putf('<I', indices_count)    # indices count

        for index in range(0, indices_count, 3):
            packed_writer.data.extend(ib[index * 2 : index * 2 + 2])
            packed_writer.data.extend(ib[index * 2 + 4 : index * 2 + 6])
            packed_writer.data.extend(ib[index * 2 + 2 : index * 2 + 4])

    return packed_writer


def write_level_geom_vb(vbs):
    packed_writer = xray_io.PackedWriter()

    packed_writer.putf('<I', len(vbs))    # vertex buffers count

    for vb in vbs:
        if vb.vertex_format == 'NORMAL':
            offsets = (0, 12, 16, 20, 24, 28)    # normal visual vertex buffer offsets
            usage_indices = (0, 0, 0, 0, 0, 1)
            vertex_type = fmt.VERTEX_TYPE_BRUSH
        elif vb.vertex_format == 'TREE':
            offsets = (0, 12, 16, 20, 24)
            usage_indices = (0, 0, 0, 0, 0)
            vertex_type = fmt.VERTEX_TYPE_TREE
        elif vb.vertex_format == 'COLOR':
            offsets = (0, 12, 16, 20, 24, 28)
            usage_indices = (0, 0, 0, 0, 0, 0)
            vertex_type = fmt.VERTEX_TYPE_COLOR
        elif vb.vertex_format == 'FASTPATH':
            offsets = (0, )
            usage_indices = (0, )
            vertex_type = fmt.VERTEX_TYPE_FASTPATH
        else:
            raise BaseException('Unknown VB format:', vb.vertex_format)

        for index, (usage, type_) in enumerate(vertex_type):
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

        packed_writer.putf('<I', vb.vertex_count)    # vertices count

        if vb.vertex_format == 'NORMAL':
            for vertex_index in range(vb.vertex_count):
                vertex_pos = vb.position[vertex_index * 12 : vertex_index * 12 + 12]
                packed_writer.data.extend(vertex_pos)
                packed_writer.putf(
                    '4B',
                    vb.normal[vertex_index * 3],
                    vb.normal[vertex_index * 3 + 1],
                    vb.normal[vertex_index * 3 + 2],
                    vb.color_hemi[vertex_index]
                )    # normal, hemi
                uv_fix = vb.uv_fix[vertex_index * 2 : vertex_index * 2 + 2]
                # tangent
                packed_writer.putf(
                    '4B',
                    vb.tangent[vertex_index * 3],
                    vb.tangent[vertex_index * 3 + 1],
                    vb.tangent[vertex_index * 3 + 2],
                    uv_fix[0]
                )
                # binormal
                packed_writer.putf(
                    '4B',
                    vb.binormal[vertex_index * 3],
                    vb.binormal[vertex_index * 3 + 1],
                    vb.binormal[vertex_index * 3 + 2],
                    uv_fix[1]
                )
                # texture coordinate
                packed_writer.data.extend(vb.uv[vertex_index * 4 : vertex_index * 4 + 4])
                # light map texture coordinate
                packed_writer.data.extend(vb.uv_lmap[vertex_index * 4 : vertex_index * 4 + 4])

        elif vb.vertex_format == 'TREE':
            for vertex_index in range(vb.vertex_count):
                vertex_pos = vb.position[vertex_index * 12 : vertex_index * 12 + 12]
                packed_writer.data.extend(vertex_pos)
                packed_writer.putf(
                    '4B',
                    vb.normal[vertex_index * 3],
                    vb.normal[vertex_index * 3 + 1],
                    vb.normal[vertex_index * 3 + 2],
                    vb.color_hemi[vertex_index]
                )    # normal, hemi
                uv_fix = vb.uv_fix[vertex_index * 2 : vertex_index * 2 + 2]
                # tangent
                packed_writer.putf(
                    '4B',
                    vb.tangent[vertex_index * 3],
                    vb.tangent[vertex_index * 3 + 1],
                    vb.tangent[vertex_index * 3 + 2],
                    uv_fix[0]
                )
                # binormal
                packed_writer.putf(
                    '4B',
                    vb.binormal[vertex_index * 3],
                    vb.binormal[vertex_index * 3 + 1],
                    vb.binormal[vertex_index * 3 + 2],
                    uv_fix[1]
                )
                # texture coordinate
                packed_writer.data.extend(vb.uv[vertex_index * 4 : vertex_index * 4 + 4])
                # tree shader data (wind coefficient and unused 2 bytes)
                frac = vb.shader_data[vertex_index * 2 : vertex_index * 2 + 2]
                frac.extend((0, 0))
                packed_writer.data.extend(frac)

        elif vb.vertex_format == 'COLOR':
            for vertex_index in range(vb.vertex_count):
                vertex_pos = vb.position[vertex_index * 12 : vertex_index * 12 + 12]
                packed_writer.data.extend(vertex_pos)
                packed_writer.putf(
                    '4B',
                    vb.normal[vertex_index * 3],
                    vb.normal[vertex_index * 3 + 1],
                    vb.normal[vertex_index * 3 + 2],
                    vb.color_hemi[vertex_index]
                )    # normal, hemi
                uv_fix = vb.uv_fix[vertex_index * 2 : vertex_index * 2 + 2]
                # tangent
                packed_writer.putf(
                    '4B',
                    vb.tangent[vertex_index * 3],
                    vb.tangent[vertex_index * 3 + 1],
                    vb.tangent[vertex_index * 3 + 2],
                    uv_fix[0]
                )
                # binormal
                packed_writer.putf(
                    '4B',
                    vb.binormal[vertex_index * 3],
                    vb.binormal[vertex_index * 3 + 1],
                    vb.binormal[vertex_index * 3 + 2],
                    uv_fix[1]
                )
                # vertex color
                packed_writer.putf(
                    '4B',
                    vb.color_light[vertex_index * 3],
                    vb.color_light[vertex_index * 3 + 1],
                    vb.color_light[vertex_index * 3 + 2],
                    vb.color_sun[vertex_index]
                )
                # texture coordinate
                packed_writer.data.extend(vb.uv[vertex_index * 4 : vertex_index * 4 + 4])

        elif vb.vertex_format == 'FASTPATH':
            for vertex_index in range(vb.vertex_count):
                vertex_pos = vb.position[vertex_index * 12 : vertex_index * 12 + 12]
                packed_writer.data.extend(vertex_pos)

    return packed_writer


def write_level_geom(chunked_writer, vbs, ibs):
    header_packed_writer = write_header()
    chunked_writer.put(fmt.Chunks.HEADER, header_packed_writer)
    del header_packed_writer

    vb_packed_writer = write_level_geom_vb(vbs)
    chunked_writer.put(fmt.Chunks.VB, vb_packed_writer)
    del vb_packed_writer

    ib_packed_writer = write_level_geom_ib(ibs)
    chunked_writer.put(fmt.Chunks.IB, ib_packed_writer)
    del ib_packed_writer

    swis_packed_writer = write_level_geom_swis()
    chunked_writer.put(fmt.Chunks.SWIS, swis_packed_writer)
    del swis_packed_writer


def write_sector_root(root_index):
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<I', root_index)
    return packed_writer


def write_sector_portals(sectors_map, sector_name):
    packed_writer = xray_io.PackedWriter()
    # None - when there are no sectors
    if sectors_map.get(sector_name, None):
        for portal in sectors_map[sector_name]:
            packed_writer.putf('<H', portal)
    return packed_writer


def write_sector(root_index, sectors_map, sector_name):
    chunked_writer = xray_io.ChunkedWriter()

    sector_portals_writer = write_sector_portals(sectors_map, sector_name)
    chunked_writer.put(fmt.SectorChunks.PORTALS, sector_portals_writer)    # portals

    sector_root_writer = write_sector_root(root_index)
    chunked_writer.put(fmt.SectorChunks.ROOT, sector_root_writer)    # root

    return chunked_writer


def write_shaders(level):
    texture_folder = plugin_prefs.get_preferences().textures_folder_auto
    materials = {}
    for material, shader_index in level.materials.items():
        materials[shader_index] = material
    materials_count = len(materials)
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<I', materials_count + 1)    # shaders count
    packed_writer.puts('')    # first empty shader
    for shader_index in range(materials_count):
        material = materials[shader_index]
        texture_node = material.node_tree.nodes['Image Texture']
        texture_path = utils.gen_texture_name(
            texture_node, texture_folder, level_folder=level.source_level_path
        )
        eshader = material.xray.eshader

        lmap_1_node = material.node_tree.nodes.get('Image Texture.001', None)
        lmap_2_node = material.node_tree.nodes.get('Image Texture.002', None)

        if lmap_1_node:
            lmap_1_path = lmap_1_node.image.name[0 : -4]    # cut .dds extension
        else:
            lmap_1_path = None

        if lmap_2_node:
            lmap_2_path = lmap_2_node.image.name[0 : -4]    # cut .dds extension
        else:
            lmap_2_path = None

        if lmap_1_node and lmap_2_node:
            packed_writer.puts('{0}/{1},{2},{3}'.format(
                eshader, texture_path, lmap_1_path, lmap_2_path
            ))
        elif lmap_1_node and not lmap_2_node:
            lmap_1_path = utils.gen_texture_name(
                lmap_1_node, texture_folder, level_folder=level.source_level_path
            )    # terrain\terrain_name_lm.dds file
            packed_writer.puts('{0}/{1},{2}'.format(
                eshader, texture_path, lmap_1_path
            ))
        else:
            packed_writer.puts('{0}/{1}'.format(
                eshader, texture_path
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


def write_visual_header(level, bpy_obj, visual=None, visual_type=0, shader_id=0):
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<B', ogf_fmt.FORMAT_VERSION_4)    # format version
    packed_writer.putf('<B', visual_type)
    if visual:
        # +1 - skip first empty shader
        packed_writer.putf('<H', visual.shader_index + 1)
    else:
        packed_writer.putf('<H', shader_id)    # shader id
    data = bpy_obj.xray
    bbox, (center, radius) = ogf_exp.calculate_bbox_and_bsphere(
        bpy_obj, apply_transforms=True, cache=level.bbox_cache
    )
    level.visuals_bbox[bpy_obj.name] = bbox
    level.visuals_center[bpy_obj.name] = center
    level.visuals_radius[bpy_obj.name] = radius
    write_visual_bounding_box(packed_writer, bpy_obj, bbox)
    write_visual_bounding_sphere(packed_writer, bpy_obj, center, radius)
    return packed_writer


def get_bbox_center(bbox):
    bbox_min = bbox[0]
    bbox_max = bbox[6]
    bbox_center = [
        bbox_max[0] - (bbox_max[0] - bbox_min[0]) / 2,
        bbox_max[1] - (bbox_max[1] - bbox_min[1]) / 2,
        bbox_max[2] - (bbox_max[2] - bbox_min[2]) / 2
    ]
    return bbox_center


def find_distance(vertex_1, vertex_2):
    distance = (
        (vertex_2[0] - vertex_1[0]) ** 2 + \
        (vertex_2[1] - vertex_1[1]) ** 2 + \
        (vertex_2[2] - vertex_1[2]) ** 2
    ) ** (1 / 2)
    return distance


MAX_TILE = 16
QUANT = 32768 / MAX_TILE


def clamp(value, min_value, max_value):
    if value > max_value:
        value = max_value
    elif value < min_value:
        value = min_value
    return value


def quant_value(float_value):
    t = int(float_value * QUANT)
    t = clamp(t, -32768, 32767)
    return t


def get_tex_coord_correct(tex_coord_f, tex_coord_h, uv_coeff):
    if tex_coord_f > 0:
        tex_coord_diff = tex_coord_f - (tex_coord_h / uv_coeff)
    else:
        tex_coord_diff = (1 + (tex_coord_f * uv_coeff - tex_coord_h)) / uv_coeff
        tex_coord_h -= 1

    tex_correct = (255 * 0x8000 * tex_coord_diff) / 32
    return int(round(tex_correct, 0)), tex_coord_h


def write_gcontainer(bpy_obj, vbs, ibs, level):
    visual = Visual()
    material = bpy_obj.data.materials[0]
    two_sided = material.xray.flags_twosided
    if level.materials.get(material, None) is None:
        level.materials[material] = level.active_material_index
        visual.shader_index = level.active_material_index
        level.active_material_index += 1
    else:
        visual.shader_index = level.materials[material]

    packed_writer = xray_io.PackedWriter()

    # multiple usage visuals
    gcontainer = level.saved_visuals.get(bpy_obj.data.name, None)
    if gcontainer:
        packed_writer.putf('<I', gcontainer[0])    # vb_index
        packed_writer.putf('<I', gcontainer[1])    # vb_offset
        packed_writer.putf('<I', gcontainer[2])    # vb_size

        packed_writer.putf('<I', gcontainer[3])    # ib_index
        packed_writer.putf('<I', gcontainer[4])    # ib_offset
        packed_writer.putf('<I', gcontainer[5])    # ib_size

        return packed_writer, visual

    bm = bmesh.new()
    bm.from_mesh(bpy_obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    if two_sided:
        dupli_geom = bmesh.ops.duplicate(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:])
        geom = dupli_geom['geom']
        dupli_faces = []
        for element in geom:
            if isinstance(element, bmesh.types.BMFace):
                dupli_faces.append(element)
        bmesh.ops.reverse_faces(bm, faces=dupli_faces)
    export_mesh = bpy.data.meshes.new('temp_mesh')
    export_mesh.use_auto_smooth = True
    export_mesh.auto_smooth_angle = math.pi
    bm.to_mesh(export_mesh)
    export_mesh.calc_normals_split()

    uv_layer = bm.loops.layers.uv['Texture']
    uv_layer_lmap = bm.loops.layers.uv.get('Light Map', None)
    vertex_color_sun = bm.loops.layers.color.get('Sun', None)
    vertex_color_hemi = bm.loops.layers.color.get('Hemi', None)
    vertex_color_light = bm.loops.layers.color.get('Light', None)
    export_mesh.calc_tangents(uvmap=uv_layer.name)

    vertex_size = 32
    if vertex_color_sun:
        vertex_format = 'COLOR'
    elif uv_layer_lmap:
        vertex_format = 'NORMAL'
    else:
        vertex_format = 'TREE'

    # find vertex buffer
    if vbs:
        vb = None
        for vertex_buffer in vbs:
            if vertex_buffer.vertex_format == vertex_format:
                if vertex_buffer.vertex_count * vertex_size > TWO_MEGABYTES:    # vb size 2 MB
                    continue
                else:
                    vb = vertex_buffer
                    break
        if vb is None:
            vb = VertexBuffer()
            vb.vertex_format = vertex_format
            vbs.append(vb)
            level.vbs_offsets.append(0)
    else:
        vb = VertexBuffer()
        vb.vertex_format = vertex_format
        vbs.append(vb)
        level.vbs_offsets.append(0)

    # find indices buffer
    vertex_index_size = 2
    if ibs:
        ib = ibs[-1]
        ib_offset = level.ibs_offsets[-1]
        indices_buffer_index = ibs.index(ib)
        if len(ib) > TWO_MEGABYTES:
            ib = bytearray()
            ibs.append(ib)
            ib_offset = 0
            indices_buffer_index += 1
            level.ibs_offsets.append(ib_offset)
    else:
        ib = bytearray()
        ibs.append(ib)
        ib_offset = 0
        level.ibs_offsets.append(ib_offset)
        indices_buffer_index = 0

    vertices_count = 0
    indices_count = 0
    vertex_index = 0

    unique_verts = {}
    verts_indices = {}
    for face in bm.faces:
        for loop in face.loops:
            vert = loop.vert
            vert_co = (vert.co[0], vert.co[1], vert.co[2])
            split_normal = export_mesh.loops[loop.index].normal
            normal = (split_normal[0], split_normal[1], split_normal[2])
            uv = loop[uv_layer].uv[0], loop[uv_layer].uv[1]
            # UV-LightMaps
            if uv_layer_lmap:
                uv_lmap = loop[uv_layer_lmap].uv[0], loop[uv_layer_lmap].uv[1]
            else:
                uv_lmap = (0.0, 0.0)
            # Vertex Color Hemi
            if vertex_color_hemi:
                hemi = loop[vertex_color_hemi][0]
            else:
                hemi = 0
            # Vertex Color Sun
            if vertex_color_sun:
                sun = loop[vertex_color_sun][0]
            else:
                sun = 0
            # Vertex Color Light
            if vertex_color_light:
                light = loop[vertex_color_light]
            else:
                light = (0, 0, 0)
            if unique_verts.get(vert_co, None):
                if not (uv, uv_lmap, normal, hemi, sun, light) in unique_verts[vert_co]:
                    unique_verts[vert_co].append((uv, uv_lmap, normal, hemi, sun, light))
                    verts_indices[vert_co].append(vertex_index)
                    vertex_index += 1
            else:
                unique_verts[vert_co] = [(uv, uv_lmap, normal, hemi, sun, light), ]
                verts_indices[vert_co] = [vertex_index, ]
                vertex_index += 1

    vertex_index = 0
    saved_verts = set()
    if uv_layer_lmap or vertex_color_sun:
        uv_coeff = fmt.UV_COEFFICIENT
    else:
        uv_coeff = fmt.UV_COEFFICIENT_2
    # tree shader params
    frac_low = get_bbox_center(bpy_obj.bound_box)
    frac_low[2] = bpy_obj.bound_box[0][2]
    frac_y_size = bpy_obj.bound_box[6][2] - bpy_obj.bound_box[0][2]
    for face in bm.faces:
        for loop in face.loops:
            vert = loop.vert
            vert_co = (vert.co[0], vert.co[1], vert.co[2])
            vert_data = unique_verts[vert_co]
            uv = loop[uv_layer].uv
            split_normal = export_mesh.loops[loop.index].normal
            if uv_layer_lmap:
                uv_lmap = loop[uv_layer_lmap].uv
            else:
                uv_lmap = (0.0, 0.0)
            # Vertex Color Hemi
            if vertex_color_hemi:
                hemi = loop[vertex_color_hemi][0]
            else:
                hemi = 0
            # Vertex Color Sun
            if vertex_color_sun:
                sun = loop[vertex_color_sun][0]
            else:
                sun = 0
            # Vertex Color Light
            if vertex_color_light:
                light = loop[vertex_color_light]
            else:
                light = (0, 0, 0)
            for index, data in enumerate(vert_data):
                if data[0] == (uv[0], uv[1]) and \
                        data[1] == (uv_lmap[0], uv_lmap[1]) and \
                        data[2] == (split_normal[0], split_normal[1], split_normal[2]) and \
                        data[3] == hemi and data[4] == sun and data[5] == light:
                    tex_uv, tex_uv_lmap, normal, hemi, sun, light = data
                    vert_index = verts_indices[vert_co][index]
                    break
            packed_vertex_index = struct.pack('<H', vert_index)
            ib.extend(packed_vertex_index)
            indices_count += 1
            if not vert_index in saved_verts:
                vb.vertex_count += 1
                saved_verts.add(vert_index)
                vertex_index += 1
                vertices_count += 1
                packed_co = struct.pack('<3f', vert.co[0], vert.co[2], vert.co[1])
                vb.position.extend(packed_co)
                vb.normal.extend((
                    int(round(((normal[1] + 1.0) / 2) * 255, 0)),
                    int(round(((normal[2] + 1.0) / 2) * 255, 0)),
                    int(round(((normal[0] + 1.0) / 2) * 255, 0))
                ))
                tangent = export_mesh.loops[loop.index].tangent
                vb.tangent.extend((
                    int(round(((tangent[1] + 1.0) / 2) * 255, 0)),
                    int(round(((tangent[2] + 1.0) / 2) * 255, 0)),
                    int(round(((tangent[0] + 1.0) / 2) * 255, 0))
                ))
                normal = mathutils.Vector(normal)
                binormal = normal.cross(tangent).normalized()
                vb.binormal.extend((
                    int(round(((binormal[1] + 1.0) / 2) * 255, 0)),
                    int(round(((binormal[2] + 1.0) / 2) * 255, 0)),
                    int(round(((binormal[0] + 1.0) / 2) * 255, 0))
                ))
                # vertex color light
                vb.color_hemi.append(int(round(hemi * 255, 0)))
                if vertex_color_sun:
                    vb.color_sun.append(int(round(sun * 255, 0)))
                    vb.color_light.extend((
                        (int(round(light[2] * 255, 0))),
                        (int(round(light[1] * 255, 0))),
                        (int(round(light[0] * 255, 0)))
                    ))
                # uv
                tex_coord_u = int(tex_uv[0] * uv_coeff)
                tex_coord_v = int((1 - tex_uv[1]) * uv_coeff)
                # uv correct
                tex_coord_u_correct, tex_coord_u = get_tex_coord_correct(tex_uv[0], tex_coord_u, uv_coeff)
                tex_coord_v_correct, tex_coord_v = get_tex_coord_correct(1 - tex_uv[1], tex_coord_v, uv_coeff)
                pw = xray_io.PackedWriter()
                pw.putf('<2B', tex_coord_u_correct, tex_coord_v_correct)

                # set uv limits
                if tex_coord_u > 0x7fff:
                    tex_coord_u = 0x7fff
                elif tex_coord_u < -0x8000:
                    tex_coord_u = -0x8000

                if tex_coord_v > 0x7fff:
                    tex_coord_v = 0x7fff
                elif tex_coord_v < -0x8000:
                    tex_coord_v = -0x8000

                packed_uv = struct.pack('<2h', tex_coord_u, tex_coord_v)
                vb.uv.extend(packed_uv)
                packed_uv_fix = struct.pack('<2B', tex_coord_u_correct, tex_coord_v_correct)
                vb.uv_fix.extend(packed_uv_fix)
                if uv_layer_lmap:
                    lmap_u = int(round(tex_uv_lmap[0] * fmt.LIGHT_MAP_UV_COEFFICIENT, 0))
                    lmap_v = int(round((1 - tex_uv_lmap[1]) * fmt.LIGHT_MAP_UV_COEFFICIENT, 0))
                    packed_uv_lmap = struct.pack('<2h', lmap_u, lmap_v)
                    vb.uv_lmap.extend(packed_uv_lmap)
                # tree shader data (wind coefficient)
                if not (uv_layer_lmap or vertex_color_sun or vertex_color_light):
                    f1 = (vert.co[2] - frac_low[2]) / frac_y_size
                    f2 = find_distance(vert.co, frac_low) / frac_y_size
                    frac = quant_value((f1 + f2) / 2)
                    packed_shader_data = struct.pack('<H', frac)
                    vb.shader_data.extend(packed_shader_data)    # wind coefficient

    vertex_buffer_index = vbs.index(vb)
    packed_writer.putf('<I', vertex_buffer_index)    # vb_index
    packed_writer.putf('<I', level.vbs_offsets[vertex_buffer_index])    # vb_offset
    packed_writer.putf('<I', vertices_count)    # vb_size

    packed_writer.putf('<I', indices_buffer_index)    # ib_index
    packed_writer.putf('<I', ib_offset)    # ib_offset
    packed_writer.putf('<I', indices_count)    # ib_size

    level.saved_visuals[bpy_obj.data.name] = (
        # vertices info
        vertex_buffer_index,
        level.vbs_offsets[vertex_buffer_index],
        vertices_count,

        # indices info
        indices_buffer_index,
        ib_offset,
        indices_count
    )

    level.vbs_offsets[vertex_buffer_index] += vertices_count
    level.ibs_offsets[-1] += indices_count

    bpy.data.meshes.remove(export_mesh)

    return packed_writer, visual


def write_ogf_color(packed_writer, bpy_obj, mode='SCALE'):
    if mode == 'SCALE':
        rgb = bpy_obj.xray.level.color_scale_rgb
        hemi = bpy_obj.xray.level.color_scale_hemi
        sun = bpy_obj.xray.level.color_scale_sun
    elif mode == 'BIAS':
        rgb = bpy_obj.xray.level.color_bias_rgb
        hemi = bpy_obj.xray.level.color_bias_hemi
        sun = bpy_obj.xray.level.color_bias_sun
    else:
        raise BaseException('Unknown ogf color mode: {}'.format(mode))
    packed_writer.putf('<3f', *rgb)    # rgb
    packed_writer.putf('<f', sum(hemi) / 3)    # hemi
    packed_writer.putf('<f', sum(sun) / 3)    # sun


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
    write_ogf_color(packed_writer, bpy_obj, mode='SCALE')
    write_ogf_color(packed_writer, bpy_obj, mode='BIAS')

    return packed_writer


def write_fastpath_gcontainer(fastpath_obj, fp_vbs, fp_ibs, level):
    packed_writer = xray_io.PackedWriter()

    bm = bmesh.new()
    bm.from_mesh(fastpath_obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    vertex_size = 12
    vertex_format = 'FASTPATH'

    # find fast path vertex buffer
    if fp_vbs:
        vb = None
        for vertex_buffer in fp_vbs:
            if vertex_buffer.vertex_format == vertex_format:
                if vertex_buffer.vertex_count * vertex_size > TWO_MEGABYTES:    # vb size 2 MB
                    continue
                else:
                    vb = vertex_buffer
                    break
        if vb is None:
            vb = VertexBuffer()
            vb.vertex_format = vertex_format
            fp_vbs.append(vb)
            level.fp_vbs_offsets.append(0)
    else:
        vb = VertexBuffer()
        vb.vertex_format = vertex_format
        fp_vbs.append(vb)
        level.fp_vbs_offsets.append(0)

    # find indices buffer
    vertex_index_size = 2
    if fp_ibs:
        ib = fp_ibs[-1]
        ib_offset = level.fp_ibs_offsets[-1]
        indices_buffer_index = fp_ibs.index(ib)
        if len(ib) > TWO_MEGABYTES:
            ib = bytearray()
            fp_ibs.append(ib)
            ib_offset = 0
            indices_buffer_index += 1
            level.fp_ibs_offsets.append(ib_offset)
    else:
        ib = bytearray()
        fp_ibs.append(ib)
        ib_offset = 0
        level.fp_ibs_offsets.append(ib_offset)
        indices_buffer_index = 0

    vertices_count = 0
    indices_count = 0
    vertex_index = 0

    unique_verts = {}
    verts_indices = {}
    for face in bm.faces:
        for vert in face.verts:
            vert_co = (vert.co[0], vert.co[1], vert.co[2])

            if not unique_verts.get(vert_co, None):
                unique_verts[vert_co] = vertex_index
                verts_indices[vert.index] = vertex_index
                packed_co = struct.pack('<3f', vert_co[0], vert_co[2], vert_co[1])
                vb.position.extend(packed_co)
                vb.vertex_count += 1
                vertices_count += 1
                vertex_index += 1
            else:
                duplicate_vertex_index = unique_verts[vert_co]
                verts_indices[vert.index] = duplicate_vertex_index

    for face in bm.faces:
        for vert in face.verts:
            vert_index = verts_indices[vert.index]
            packed_vert_index = struct.pack('<H', vert_index)
            ib.extend(packed_vert_index)
            indices_count += 1

    vertex_buffer_index = fp_vbs.index(vb)
    packed_writer.putf('<I', vertex_buffer_index)    # vb_index
    packed_writer.putf('<I', level.fp_vbs_offsets[vertex_buffer_index])    # vb_offset
    packed_writer.putf('<I', vertices_count)    # vb_size

    packed_writer.putf('<I', indices_buffer_index)    # ib_index
    packed_writer.putf('<I', ib_offset)    # ib_offset
    packed_writer.putf('<I', indices_count)    # ib_size

    level.fp_vbs_offsets[vertex_buffer_index] += vertices_count
    level.fp_ibs_offsets[-1] += indices_count

    return packed_writer


def write_fastpath(fastpath_obj, fp_vbs, fp_ibs, level):
    chunked_writer = xray_io.ChunkedWriter()
    writer = write_fastpath_gcontainer(fastpath_obj, fp_vbs, fp_ibs, level)
    chunked_writer.put(ogf_fmt.Chunks.GCONTAINER, writer)
    return chunked_writer


def write_visual(
        bpy_obj, vbs, ibs,
        hierrarhy, visuals_ids, level, fp_vbs, fp_ibs
    ):
    if bpy_obj.xray.level.visual_type == 'HIERRARHY':
        chunked_writer = write_hierrarhy_visual(
            bpy_obj, hierrarhy, visuals_ids, level
        )
        return chunked_writer
    elif bpy_obj.xray.level.visual_type == 'LOD':
        chunked_writer = write_lod_visual(
            bpy_obj, hierrarhy, visuals_ids, level
        )
        return chunked_writer
    else:
        chunked_writer = xray_io.ChunkedWriter()
        gcontainer_writer, visual = write_gcontainer(
            bpy_obj, vbs, ibs, level
        )
        if bpy_obj.xray.level.visual_type in ('TREE_ST', 'TREE_PM'):
            header_writer = write_visual_header(level, bpy_obj, visual=visual, visual_type=7)
            tree_def_2_writer = write_tree_def_2(bpy_obj, chunked_writer)
            chunked_writer.put(ogf_fmt.Chunks.HEADER, header_writer)
            chunked_writer.put(ogf_fmt.Chunks.GCONTAINER, gcontainer_writer)
            chunked_writer.put(ogf_fmt.Chunks.TREEDEF2, tree_def_2_writer)
        else:    # NORMAL or PROGRESSIVE visual
            header_writer = write_visual_header(level, bpy_obj, visual=visual)
            chunked_writer.put(ogf_fmt.Chunks.HEADER, header_writer)
            chunked_writer.put(ogf_fmt.Chunks.GCONTAINER, gcontainer_writer)
            if len(bpy_obj.children) > 1:
                raise utils.AppError('Object "{}" has more than one children'.format(bpy_obj.name))
            if bpy_obj.xray.level.use_fastpath:
                fastpath_writer = write_fastpath(bpy_obj, fp_vbs, fp_ibs, level)
                chunked_writer.put(ogf_fmt.Chunks.FASTPATH, fastpath_writer)
        return chunked_writer


def write_children_l(bpy_obj, hierrarhy, visuals_ids):
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<I', len(hierrarhy[bpy_obj.name]))
    for child_obj in hierrarhy[bpy_obj.name]:
        child_index = visuals_ids[child_obj]
        packed_writer.putf('<I', child_index)
    return packed_writer


def write_hierrarhy_visual(bpy_obj, hierrarhy, visuals_ids, level):
    visual_writer = xray_io.ChunkedWriter()
    header_writer = write_visual_header(
        level, bpy_obj, visual_type=ogf_fmt.ModelType.HIERRARHY, shader_id=0
    )
    visual_writer.put(ogf_fmt.Chunks.HEADER, header_writer)
    children_l_writer = write_children_l(bpy_obj, hierrarhy, visuals_ids)
    visual_writer.put(ogf_fmt.Chunks.CHILDREN_L, children_l_writer)
    return visual_writer


def write_rgb_hemi(red, green, blue, hemi):
    red = int(round(red * 0xff, 0))
    green = int(round(green * 0xff, 0))
    blue = int(round(blue * 0xff, 0))
    hemi = int(round(hemi * 0xff, 0))
    int_color = \
        ((hemi & 0xff) << 24) | \
        ((red & 0xff) << 16) | \
        ((green & 0xff) << 8) | \
        (blue & 0xff)
    return int_color


def write_lod_def_2(bpy_obj, hierrarhy, visuals_ids, level):
    packed_writer = xray_io.PackedWriter()
    me = bpy_obj.data
    uv_layer = me.uv_layers['Texture']
    rgb_layer = me.vertex_colors['Light']
    hemi_layer = me.vertex_colors['Hemi']
    sun_layer = me.vertex_colors['Sun']

    visual = Visual()
    material = bpy_obj.data.materials[0]
    if level.materials.get(material, None) is None:
        level.materials[material] = level.active_material_index
        visual.shader_index = level.active_material_index
        level.active_material_index += 1
    else:
        visual.shader_index = level.materials[material]

    if len(me.polygons) != 8:
        raise BaseException('LOD mesh "{}" has not 8 polygons'.format(bpy_obj.data))
    if len(me.vertices) != 32:
        raise BaseException('LOD mesh "{}"  has not 32 vertices'.format(bpy_obj.data))
    for face_index in range(8):
        face = me.polygons[face_index]
        for face_vertex_index in range(4):
            vert_index = face.vertices[face_vertex_index]
            vert = me.vertices[vert_index]
            packed_writer.putf('<3f', vert.co.x, vert.co.z, vert.co.y)
            loop_index = range(face.loop_start, face.loop_start + face.loop_total)[face_vertex_index]
            uv = uv_layer.data[loop_index].uv
            packed_writer.putf('<2f', uv[0], 1 - uv[1])
            # export vertex light
            rgb = rgb_layer.data[loop_index].color
            red = rgb[0]
            green = rgb[1]
            blue = rgb[2]
            hemi = sum(hemi_layer.data[loop_index].color[0 : 3]) / 3
            sun = sum(sun_layer.data[loop_index].color[0 : 3]) / 3
            packed_writer.putf('<I', write_rgb_hemi(red, green, blue, hemi))
            packed_writer.putf('<B', int(round(sun * 0xff, 0)))
            # fill with bytes so that the size of the structure is a multiple of 4
            packed_writer.putf('<3B', 0, 0, 0)
    return packed_writer, visual


def write_lod_visual(bpy_obj, hierrarhy, visuals_ids, level):
    visual_writer = xray_io.ChunkedWriter()

    children_l_writer = write_children_l(bpy_obj, hierrarhy, visuals_ids)
    lod_def_2_writer, visual = write_lod_def_2(
        bpy_obj, hierrarhy, visuals_ids, level
    )
    header_writer = write_visual_header(
        level, bpy_obj, visual=visual, visual_type=ogf_fmt.ModelType.LOD
    )

    visual_writer.put(ogf_fmt.Chunks.HEADER, header_writer)
    visual_writer.put(ogf_fmt.Chunks.CHILDREN_L, children_l_writer)
    visual_writer.put(ogf_fmt.Chunks.LODDEF2, lod_def_2_writer)

    return visual_writer


def write_visual_children(
        chunked_writer, vbs, ibs,
        visual_index, hierrarhy,
        visuals_ids, visuals, level, fp_vbs, fp_ibs
    ):

    for visual_obj in visuals:
        visual_chunked_writer = write_visual(
            visual_obj, vbs, ibs,
            hierrarhy, visuals_ids, level, fp_vbs, fp_ibs
        )
        if visual_chunked_writer:
            chunked_writer.put(visual_index, visual_chunked_writer)
            visual_index += 1
    return visual_index


def find_hierrarhy(visual_obj, visuals_hierrarhy, visual_index, visuals):
    visuals.append(visual_obj)
    visuals_hierrarhy[visual_obj.name] = []
    children_objs = []
    for child_obj in visual_obj.children:
        children_objs.append(child_obj)
        visual_index += 1
        visuals_hierrarhy[visual_obj.name].append(child_obj)

    for child_child_obj in children_objs:
        if child_child_obj.xray.level.object_type == 'VISUAL':
            if child_child_obj.xray.level.visual_type != 'FASTPATH':
                visuals_hierrarhy, visual_index = find_hierrarhy(
                    child_child_obj, visuals_hierrarhy, visual_index, visuals
                )
    return visuals_hierrarhy, visual_index


def write_visuals(level_object, sectors_map, level):
    chunked_writer = xray_io.ChunkedWriter()
    sectors_chunked_writer = xray_io.ChunkedWriter()
    visuals_collection = bpy.data.collections['Visuals']
    vertex_buffers = []
    indices_buffers = []
    fastpath_vertex_buffers = []
    fastpath_indices_buffers = []
    visual_index = 0
    sector_id = 0
    visuals_hierrarhy = {}
    visuals = []
    for child_obj in level_object.children:
        if child_obj.name.startswith('sectors'):
            for sector_obj in child_obj.children:
                for obj in sector_obj.children:
                    if obj.xray.level.object_type == 'VISUAL':
                        visuals_hierrarhy, visual_index = find_hierrarhy(
                            obj, visuals_hierrarhy, visual_index, visuals
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
                level.sectors_indices[sector_obj.name] = sector_id
                for root_obj in sector_obj.children:
                    if root_obj.xray.level.object_type == 'VISUAL':
                        # write sector
                        root_index = visuals_ids[root_obj]
                        sector_chunked_writer = write_sector(
                            root_index, sectors_map, sector_obj.name
                        )
                        sectors_chunked_writer.put(sector_id, sector_chunked_writer)
                    elif root_obj.xray.level.object_type == 'CFORM':
                        level.cform_objects[sector_id] = root_obj
                sector_id += 1

    visual_index = write_visual_children(
        chunked_writer, vertex_buffers, indices_buffers,
        visual_index, visuals_hierrarhy, visuals_ids, visuals, level,
        fastpath_vertex_buffers, fastpath_indices_buffers
    )
    return (
        chunked_writer, vertex_buffers, indices_buffers,
        sectors_chunked_writer, fastpath_vertex_buffers,
        fastpath_indices_buffers
    )


def write_glow(packed_writer, glow_obj, level):
    # position
    packed_writer.putf(
        '<3f',
        glow_obj.location[0],
        glow_obj.location[2],
        glow_obj.location[1]
    )
    packed_writer.putf('<f', glow_obj.dimensions[0] / 2)    # radius
    if not len(glow_obj.data.materials):
        raise BaseException('glow object "{}" has no material'.format(glow_obj.name))
    material = glow_obj.data.materials[0]
    if level.materials.get(material, None) is None:
        level.materials[material] = level.active_material_index
        shader_index = level.active_material_index
        level.active_material_index += 1
    else:
        shader_index = level.materials[material]
    # shader index
    # +1 - skip first empty shader
    packed_writer.putf('<H', shader_index + 1)


def write_glows(level_object, level):
    packed_writer = xray_io.PackedWriter()
    for child_obj in level_object.children:
        if child_obj.name.startswith('glows'):
            for glow_obj in child_obj.children:
                write_glow(packed_writer, glow_obj, level)
    return packed_writer


def write_light(level_object):
    packed_writer = xray_io.PackedWriter()
    for child_obj in level_object.children:
        if child_obj.name.startswith('light dynamic'):
            for light_obj in child_obj.children:
                data = light_obj.xray.level
                packed_writer.putf('I', data.controller_id)
                packed_writer.putf('I', data.light_type)
                packed_writer.putf('4f', *data.diffuse)
                packed_writer.putf('4f', *data.specular)
                packed_writer.putf('4f', *data.ambient)
                packed_writer.putf(
                    '3f',
                    light_obj.location[0],
                    light_obj.location[2],
                    light_obj.location[1]
                )
                euler = light_obj.matrix_world.to_euler('YXZ')
                matrix = euler.to_matrix().to_3x3()
                direction = (matrix[0][1], matrix[2][1], matrix[1][1])
                packed_writer.putf('3f', direction[0], direction[1], direction[2])
                packed_writer.putf('f', data.range_)
                packed_writer.putf('f', data.falloff)
                packed_writer.putf('f', data.attenuation_0)
                packed_writer.putf('f', data.attenuation_1)
                packed_writer.putf('f', data.attenuation_2)
                packed_writer.putf('f', data.theta)
                packed_writer.putf('f', data.phi)
            return packed_writer


def append_portal(sectors_map, sector_index, portal_index):
    if not sectors_map.get(sector_index, None) is None:
        sectors_map[sector_index].append(portal_index)
    else:
        sectors_map[sector_index] = [portal_index, ]


def write_portals(level, level_object):
    packed_writer = xray_io.PackedWriter()
    for child_obj in level_object.children:
        if child_obj.name.startswith('portals'):
            for portal_index, portal_obj in enumerate(child_obj.children):
                packed_writer.putf('<H', level.sectors_indices[portal_obj.xray.level.sector_front])
                packed_writer.putf('<H', level.sectors_indices[portal_obj.xray.level.sector_back])
                for vertex in portal_obj.data.vertices:
                    packed_writer.putf(
                        '<3f', vertex.co.x, vertex.co.z, vertex.co.y
                    )
                vertices_count = len(portal_obj.data.vertices)
                for vertex_index in range(vertices_count, 6):
                    packed_writer.putf('<3f', 0.0, 0.0, 0.0)
                packed_writer.putf('<I', vertices_count)
    return packed_writer


def get_sectors_map(level_object):
    sectors_map = {}
    for child_obj in level_object.children:
        if child_obj.name.startswith('portals'):
            for portal_index, portal_obj in enumerate(child_obj.children):
                append_portal(
                    sectors_map, portal_obj.xray.level.sector_front, portal_index
                )
                append_portal(
                    sectors_map, portal_obj.xray.level.sector_back, portal_index
                )
    return sectors_map


def write_header():
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<H', fmt.VERSION_14)
    packed_writer.putf('<H', 0)    # quality
    return packed_writer


def write_level(chunked_writer, level_object, file_path):
    level = Level()
    level.source_level_path = level_object.xray.level.source_path

    # header
    header_writer = write_header()
    chunked_writer.put(fmt.Chunks.HEADER, header_writer)
    del header_writer

    sectors_map = get_sectors_map(level_object)

    # visuals
    (visuals_writer, vbs, ibs,
    sectors_chunked_writer, fp_vbs, fp_ibs) = write_visuals(
        level_object, sectors_map, level
    )

    # portals
    portals_writer = write_portals(level, level_object)
    chunked_writer.put(fmt.Chunks.PORTALS, portals_writer)
    del portals_writer

    # light dynamic
    light_writer = write_light(level_object)
    chunked_writer.put(fmt.Chunks.LIGHT_DYNAMIC, light_writer)
    del light_writer

    # glow
    glows_writer = write_glows(level_object, level)
    chunked_writer.put(fmt.Chunks.GLOWS, glows_writer)
    del glows_writer

    # write visuals chunk
    chunked_writer.put(fmt.Chunks.VISUALS, visuals_writer)
    del visuals_writer

    # shaders
    shaders_writer = write_shaders(level)
    chunked_writer.put(fmt.Chunks.SHADERS, shaders_writer)
    del shaders_writer

    # sectors
    chunked_writer.put(fmt.Chunks.SECTORS, sectors_chunked_writer)
    del sectors_chunked_writer

    return vbs, ibs, fp_vbs, fp_ibs, level


def get_bbox(bbox_1, bbox_2, function):
    bbox_x = function(bbox_1[0], bbox_2[0])
    bbox_y = function(bbox_1[1], bbox_2[1])
    bbox_z = function(bbox_1[2], bbox_2[2])
    return (bbox_x, bbox_y, bbox_z)


def write_level_cform(packed_writer, level):
    sectors_count = len(level.cform_objects)
    cform_header_packed_writer = xray_io.PackedWriter()
    cform_header_packed_writer.putf('<I', 4)    # version
    vertices_packed_writer = xray_io.PackedWriter()
    tris_packed_writer = xray_io.PackedWriter()
    vertex_index_offset = 0
    faces_count = 0
    face_vert_indices = (0, 2, 1)

    materials = set()
    bbox_min = None
    bbox_max = None
    for _, cform_object in level.cform_objects.items():
        if not bbox_min:
            bbox_min = cform_object.bound_box[0]
        else:
            bbox_min = get_bbox(bbox_min, cform_object.bound_box[0], min)
        if not bbox_max:
            bbox_max = cform_object.bound_box[6]
        else:
            bbox_max = get_bbox(bbox_max, cform_object.bound_box[6], max)
        for material in cform_object.data.materials:
            materials.add(material)

    prefs = plugin_prefs.get_preferences()
    gamemtl_file_path = prefs.gamemtl_file_auto
    if os.path.exists(gamemtl_file_path):
        with open(gamemtl_file_path, 'rb') as gamemtl_file:
            gamemtl_data = gamemtl_file.read()
    else:
        gamemtl_data = b''

    game_mtls = {}
    for game_mtl_name, _, game_mtl_id in utils.parse_gamemtl(gamemtl_data):
        game_mtls[game_mtl_name] = game_mtl_id

    game_materials = {}
    for material in materials:
        gamemtl_id = game_mtls.get(material.xray.gamemtl, 0)
        game_materials[material.name] = gamemtl_id

    for sector_index in range(sectors_count):
        cform_object = level.cform_objects[sector_index]
        bm = bmesh.new()
        bm.from_mesh(cform_object.data)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        vertices_count = 0
        for vert in bm.verts:
            vertices_packed_writer.putf(
                '<3f', vert.co.x, vert.co.z, vert.co.y
            )
            vertices_count += 1
        for face in bm.faces:
            for vert_index in face_vert_indices:
                vert = face.verts[vert_index]
                tris_packed_writer.putf('<I', vert.index + vertex_index_offset)
            material = cform_object.data.materials[face.material_index]
            material_id = game_materials[material.name]
            suppress_shadows = (int(material.xray.suppress_shadows) << 14) & 0x4000
            suppress_wm = (int(material.xray.suppress_wm << 15)) & 0x8000
            cform_material = material_id | suppress_shadows | suppress_wm
            tris_packed_writer.putf('<2H', cform_material, sector_index)
            faces_count += 1
        vertex_index_offset += vertices_count

    cform_header_packed_writer.putf('<I', vertex_index_offset)    # vertices count
    cform_header_packed_writer.putf('<I', faces_count)
    cform_header_packed_writer.putf('<3f', bbox_min[0], bbox_min[2], bbox_min[1])    # bbox min
    cform_header_packed_writer.putf('<3f', bbox_max[0], bbox_max[2], bbox_max[1])    # bbox max

    packed_writer.putp(cform_header_packed_writer)
    del cform_header_packed_writer

    packed_writer.putp(vertices_packed_writer)
    del vertices_packed_writer

    packed_writer.putp(tris_packed_writer)
    del tris_packed_writer


def get_writer():
    chunked_writer = xray_io.ChunkedWriter()
    return chunked_writer


def export_file(level_object, dir_path):
    start_time = time.time()

    file_path = dir_path + os.sep + 'level'
    level_chunked_writer = get_writer()
    vbs, ibs, fp_vbs, fp_ibs, level = write_level(level_chunked_writer, level_object, file_path)

    with open(file_path, 'wb') as file:
        file.write(level_chunked_writer.data)
    del level_chunked_writer

    # geometry
    level_geom_chunked_writer = get_writer()
    write_level_geom(level_geom_chunked_writer, vbs, ibs)

    del (
        vbs, ibs, level.materials, level.visuals, level.vbs_offsets,
        level.ibs_offsets, level.saved_visuals, level.sectors_indices,
        level.visuals_bbox, level.visuals_center, level.visuals_radius,
        level.bbox_cache
    )

    with open(file_path + os.extsep + 'geom', 'wb') as file:
        file.write(level_geom_chunked_writer.data)
    del level_geom_chunked_writer

    # fast path geometry
    level_geomx_chunked_writer = get_writer()
    write_level_geom(level_geomx_chunked_writer, fp_vbs, fp_ibs)
    del fp_vbs, fp_ibs, level.fp_vbs_offsets, level.fp_ibs_offsets

    with open(file_path + os.extsep + 'geomx', 'wb') as file:
        file.write(level_geomx_chunked_writer.data)
    del level_geomx_chunked_writer

    # cform
    level_cform_packed_writer = xray_io.PackedWriter()
    write_level_cform(level_cform_packed_writer, level)
    with open(file_path + os.extsep + 'cform', 'wb') as file:
        file.write(level_cform_packed_writer.data)
    del level_cform_packed_writer, level

    print('total time: {}s'.format(time.time() - start_time))
