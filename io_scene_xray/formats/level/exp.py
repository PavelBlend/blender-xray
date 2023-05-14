# standart modules
import os
import math
import struct

# blender modules
import bpy
import bmesh
import mathutils

# addon modules
from . import fmt
from .. import ogf
from .. import xr
from ... import text
from ... import utils
from ... import log
from ... import rw


TWO_MEGABYTES = 1024 * 1024 * 2
MAX_TILE = 16
QUANT = 32768 / MAX_TILE


class Level(object):
    def __init__(self):
        self.active_material_index = 0

        self.visuals = []
        self.vbs_offsets = []
        self.ibs_offsets = []
        self.fp_vbs_offsets = []
        self.fp_ibs_offsets = []

        self.materials = {}
        self.saved_visuals = {}
        self.visuals_bbox = {}
        self.visuals_center = {}
        self.visuals_radius = {}
        self.sectors_indices = {}
        self.cform_objects = {}

        self.visuals_cache = VisualsCache()


class VertexBuffer(object):
    def __init__(self):
        self.vertex_count = 0
        self.vertex_format = None

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


class Visual(object):
    def __init__(self):
        self.shader_index = None


class VisualsCache:
    def __init__(self):
        self.bounds = {}
        self.children = {}

        # search children
        for obj in bpy.data.objects:
            self.children[obj.name] = []

        for child_obj in bpy.data.objects:
            parent = child_obj.parent
            if parent:
                self.children[parent.name].append(child_obj.name)


class ExportLevelContext():
    def __init__(self, textures_folder):
        self.textures_folder = textures_folder
        self.texname_from_path = True


def write_geom_swis(geom_writer):
    swis_writer = rw.write.PackedWriter()
    # TODO: export swis data
    swis_writer.putf('<I', 0)    # swis count
    geom_writer.put(fmt.Chunks13.SWIS, swis_writer)


def write_geom_ibs(geom_writer, ibs):
    ib_writer = rw.write.PackedWriter()

    buffers_count = len(ibs)
    ib_writer.putf('<I', buffers_count)

    for ib in ibs:
        indices_count = len(ib) // fmt.INDEX_SIZE
        ib_writer.putf('<I', indices_count)
        ib_writer.data.extend(ib)

    geom_writer.put(fmt.Chunks13.IB, ib_writer)


def write_geom_vbs(geom_writer, vbs):
    vbs_writer = rw.write.PackedWriter()

    buffers_count = len(vbs)
    vbs_writer.putf('<I', buffers_count)

    for vb in vbs:

        if vb.vertex_format == 'NORMAL':
            offsets = (0, 12, 16, 20, 24, 28)    # vertex buffer offsets
            usage_indices = (0, 0, 0, 0, 0, 1)
            vertex_type = fmt.VERTEX_TYPE_BRUSH_14

        elif vb.vertex_format == 'TREE':
            offsets = (0, 12, 16, 20, 24)
            usage_indices = (0, 0, 0, 0, 0)
            vertex_type = fmt.VERTEX_TYPE_TREE

        elif vb.vertex_format == 'COLOR':
            offsets = (0, 12, 16, 20, 24, 28)
            usage_indices = (0, 0, 0, 0, 0, 0)
            vertex_type = fmt.VERTEX_TYPE_COLOR_14

        elif vb.vertex_format == 'FASTPATH':
            offsets = (0, )
            usage_indices = (0, )
            vertex_type = fmt.VERTEX_TYPE_FASTPATH

        else:
            raise BaseException('Unknown VB format:', vb.vertex_format)

        # write buffer header
        for index, (usage, value_type) in enumerate(vertex_type):
            vbs_writer.putf('<H', 0)    # stream
            vbs_writer.putf('<H', offsets[index])    # offset
            vbs_writer.putf('<B', value_type)    # type
            vbs_writer.putf('<B', 0)    # method
            vbs_writer.putf('<B', usage)    # usage
            vbs_writer.putf('<B', usage_indices[index])    # usage_index

        vbs_writer.putf('<H', 255)    # stream
        vbs_writer.putf('<H', 0)    # offset
        vbs_writer.putf('<B', fmt.types_values[fmt.UNUSED])   # type UNUSED
        vbs_writer.putf('<B', 0)    # method
        vbs_writer.putf('<B', 0)    # usage
        vbs_writer.putf('<B', 0)    # usage_index

        vbs_writer.putf('<I', vb.vertex_count)    # vertices count

        # write vertices
        if vb.vertex_format == 'NORMAL':
            for index in range(vb.vertex_count):
                vbs_writer.data.extend(vb.position[index*12 : index*12 + 12])
                vbs_writer.data.extend((
                    *vb.normal[index*3 : index*3 + 3],
                    vb.color_hemi[index]
                ))    # normal, hemi
                uv_fix = vb.uv_fix[index*2 : index*2 + 2]
                # tangent
                vbs_writer.data.extend((
                    *vb.tangent[index*3 : index*3 + 3],
                    uv_fix[0]
                ))
                # binormal
                vbs_writer.data.extend((
                    *vb.binormal[index*3 : index*3 + 3],
                    uv_fix[1]
                ))
                # texture coordinate
                vbs_writer.data.extend(vb.uv[index*4 : index*4 + 4])
                # light map texture coordinate
                vbs_writer.data.extend(vb.uv_lmap[index*4 : index*4 + 4])

        elif vb.vertex_format == 'TREE':
            for index in range(vb.vertex_count):
                vbs_writer.data.extend(vb.position[index*12 : index*12 + 12])
                vbs_writer.data.extend((
                    *vb.normal[index*3 : index*3 + 3],
                    vb.color_hemi[index]
                ))    # normal, hemi
                uv_fix = vb.uv_fix[index*2 : index*2 + 2]
                # tangent
                vbs_writer.data.extend((
                    *vb.tangent[index*3 : index*3 + 3],
                    uv_fix[0]
                ))
                # binormal
                vbs_writer.data.extend((
                    *vb.binormal[index*3 : index*3 + 3],
                    uv_fix[1]
                ))
                # texture coordinate
                vbs_writer.data.extend(vb.uv[index*4 : index*4 + 4])
                # tree shader data (wind coefficient and unused 2 bytes)
                frac = vb.shader_data[index*2 : index*2 + 2]
                frac.extend((0, 0))
                vbs_writer.data.extend(frac)

        elif vb.vertex_format == 'COLOR':
            for index in range(vb.vertex_count):
                vbs_writer.data.extend(vb.position[index*12 : index*12 + 12])
                vbs_writer.data.extend((
                    *vb.normal[index*3 : index*3 + 3],
                    vb.color_hemi[index]
                ))    # normal, hemi
                uv_fix = vb.uv_fix[index*2 : index*2 + 2]
                # tangent
                vbs_writer.data.extend((
                    *vb.tangent[index*3 : index*3 + 3],
                    uv_fix[0]
                ))
                # binormal
                vbs_writer.data.extend((
                    *vb.binormal[index*3 : index*3 + 3],
                    uv_fix[1]
                ))
                # vertex color
                vbs_writer.data.extend((
                    *vb.color_light[index*3 : index*3 + 3],
                    vb.color_sun[index]
                ))
                # texture coordinate
                vbs_writer.data.extend(vb.uv[index*4 : index*4 + 4])

        elif vb.vertex_format == 'FASTPATH':
            vbs_writer.data.extend(vb.position)

    geom_writer.put(fmt.Chunks13.VB, vbs_writer)


def write_geom(file_path, vbs, ibs, ext):
    # level.geom/level.geomx chunked writer
    geom_writer = get_writer()

    # header
    write_header(geom_writer)

    # vertex buffers
    write_geom_vbs(geom_writer, vbs)

    # indices buffers
    write_geom_ibs(geom_writer, ibs)

    # slide window items
    write_geom_swis(geom_writer)

    # save level.geom/level.geomx file
    geom_path = file_path + os.extsep + ext
    rw.utils.save_file(geom_path, geom_writer)


def write_sector_root(sector_writer, root_index):
    root_writer = rw.write.PackedWriter()
    root_writer.putf('<I', root_index)
    sector_writer.put(fmt.SectorChunks.ROOT, root_writer)


def write_sector_portals(sector_writer, sectors_portals, sector_name):
    portals_writer = rw.write.PackedWriter()

    # None - when there are no sectors
    portals = sectors_portals.get(sector_name, None)
    if portals:
        for portal_index in portals:
            portals_writer.putf('<H', portal_index)

    sector_writer.put(fmt.SectorChunks.PORTALS, portals_writer)


def write_sector(root_index, sectors_portals, sector_name):
    sector_writer = rw.write.ChunkedWriter()

    # write portals
    write_sector_portals(sector_writer, sectors_portals, sector_name)

    # write root-visual
    write_sector_root(sector_writer, root_index)

    return sector_writer


def get_light_map_image(material, lmap_prop):
    lmap_image_name = getattr(material.xray, lmap_prop, None)

    if lmap_image_name:
        lmap_image = bpy.data.images.get(lmap_image_name, None)
        if not lmap_image:
            raise log.AppError(
                text.error.level_no_lmap,
                log.props(
                    light_map=lmap_image_name,
                    material=material.name
                )
            )
        image_path = lmap_image.filepath
        image_name = os.path.basename(image_path)
        base_name, ext = os.path.splitext(image_name)
        if ext != '.dds':
            raise log.AppError(
                text.error.level_lmap_no_dds,
                log.props(
                    image=lmap_image.name,
                    path=lmap_image.filepath,
                    extension=ext
                )
            )
        lmap_name = base_name

    else:
        lmap_image = None
        lmap_name = None

    return lmap_image, lmap_name


def write_shaders(level_writer, level):
    texture_folder = utils.version.get_preferences().textures_folder_auto

    materials = {}
    for material, shader_index in level.materials.items():
        materials[shader_index] = material

    materials_count = len(materials)
    shaders_writer = rw.write.PackedWriter()
    shaders_writer.putf('<I', materials_count + 1)    # shaders count
    shaders_writer.puts('')    # first empty shader
    context = ExportLevelContext(texture_folder)

    for shader_index in range(materials_count):
        material = materials[shader_index]
        texture_path = utils.material.get_image_relative_path(
            material,
            context,
            level_folder=level.source_level_path,
            no_err=False
        )

        eshader = material.xray.eshader

        lmap_1_image, lmap_1_name = get_light_map_image(material, 'lmap_0')
        lmap_2_image, lmap_2_name = get_light_map_image(material, 'lmap_1')

        # lightmap shader
        if lmap_1_image and lmap_2_image:
            shaders_writer.puts('{0}/{1},{2},{3}'.format(
                eshader,
                texture_path,
                lmap_1_name,
                lmap_2_name
            ))

        # terrain shader
        elif lmap_1_image and not lmap_2_image:
            lmap_1_path = utils.image.gen_texture_name(
                lmap_1_image,
                texture_folder,
                level_folder=level.source_level_path
            )
            shaders_writer.puts('{0}/{1},{2}'.format(
                eshader,
                texture_path,
                lmap_1_path
            ))

        # vertex colors shader
        else:
            shaders_writer.puts('{0}/{1}'.format(eshader, texture_path))

    level_writer.put(fmt.Chunks13.SHADERS, shaders_writer)


def write_visual_bounding_sphere(header_writer, center, radius):
    header_writer.putf('<3f', center[0], center[2], center[1])
    header_writer.putf('<f', radius)


def write_visual_bounding_box(header_writer, bbox):
    bbox_min = bbox[0]
    bbox_max = bbox[1]
    header_writer.putf('<3f', bbox_min[0], bbox_min[2], bbox_min[1])    # min
    header_writer.putf('<3f', bbox_max[0], bbox_max[2], bbox_max[1])    # max


def write_visual_header(level, bpy_obj, visual=None, visual_type=0, shader_id=0):
    header_writer = rw.write.PackedWriter()
    header_writer.putf('<B', ogf.fmt.FORMAT_VERSION_4)    # format version
    header_writer.putf('<B', visual_type)

    if visual:
        # +1 - skip first empty shader
        header_writer.putf('<H', visual.shader_index + 1)
    else:
        header_writer.putf('<H', shader_id)    # shader id

    bbox, (center, radius) = ogf.exp.calculate_bbox_and_bsphere(
        bpy_obj,
        apply_transforms=True,
        cache=level.visuals_cache
    )
    level.visuals_bbox[bpy_obj.name] = bbox
    level.visuals_center[bpy_obj.name] = center
    level.visuals_radius[bpy_obj.name] = radius

    write_visual_bounding_box(header_writer, bbox)
    write_visual_bounding_sphere(header_writer, center, radius)

    return header_writer


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


def clamp(value, min_value, max_value):
    if value > max_value:
        value = max_value
    elif value < min_value:
        value = min_value
    return value


def quant_value(float_value):
    return clamp(int(float_value * QUANT), -32768, 32767)


def get_tex_coord_correct(coord_f, coord_h, uv_coeff):
    # coord_f - float texture coordinate
    # coord_h - unsigned 16 bit integer texture coordinate
    # uv_coeff - max unsigned 16 bit integer value for texture coordinate

    if coord_f > 0:
        diff = coord_f - (coord_h / uv_coeff)
    else:
        diff = (1 + (coord_f * uv_coeff - coord_h)) / uv_coeff
        coord_h -= 1

    tex_correct = (255 * 0x8000 * diff) / 32

    return int(round(tex_correct, 0)), coord_h


def write_gcontainer(bpy_obj, vbs, ibs, level):
    visual = Visual()
    material = bpy_obj.data.materials[0]
    if level.materials.get(material, None) is None:
        level.materials[material] = level.active_material_index
        visual.shader_index = level.active_material_index
        level.active_material_index += 1
    else:
        visual.shader_index = level.materials[material]

    packed_writer = rw.write.PackedWriter()

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
    export_mesh = bpy.data.meshes.new('temp_mesh')
    export_mesh.use_auto_smooth = True
    export_mesh.auto_smooth_angle = math.pi
    bm.to_mesh(export_mesh)
    export_mesh.calc_normals_split()

    uv_layer = bm.loops.layers.uv[material.xray.uv_texture]
    uv_layer_lmap = bm.loops.layers.uv.get(material.xray.uv_light_map, None)
    vertex_color_sun = bm.loops.layers.color.get(
        material.xray.sun_vert_color, None
    )
    vertex_color_hemi = bm.loops.layers.color.get(
        material.xray.hemi_vert_color, None
    )
    vertex_color_light = bm.loops.layers.color.get(
        material.xray.light_vert_color, None
    )
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
            if unique_verts.get(vert_co, None) is None:
                unique_verts[vert_co] = [(uv, uv_lmap, normal, hemi, sun, light), ]
                verts_indices[vert_co] = [vertex_index, ]
                vertex_index += 1
            else:
                if not (uv, uv_lmap, normal, hemi, sun, light) in unique_verts[vert_co]:
                    unique_verts[vert_co].append((uv, uv_lmap, normal, hemi, sun, light))
                    verts_indices[vert_co].append(vertex_index)
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
        face_indices = []
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
            face_indices.append(packed_vertex_index)
            indices_count += 1
            if not vert_index in saved_verts:
                vb.vertex_count += 1
                saved_verts.add(vert_index)
                vertex_index += 1
                vertices_count += 1
                packed_co = struct.pack(
                    '<3f',
                    vert.co[0],
                    vert.co[2],
                    vert.co[1]
                )
                vb.position.extend(packed_co)
                vb.normal.extend(struct.pack(
                    '<3B',
                    int(((normal[1] + 1.0) / 2) * 255),
                    int(((normal[2] + 1.0) / 2) * 255),
                    int(((normal[0] + 1.0) / 2) * 255)
                ))
                tangent = export_mesh.loops[loop.index].tangent
                vb.tangent.extend(struct.pack(
                    '<3B',
                    int(((tangent[1] + 1.0) / 2) * 255),
                    int(((tangent[2] + 1.0) / 2) * 255),
                    int(((tangent[0] + 1.0) / 2) * 255)
                ))
                normal = mathutils.Vector(normal)
                binormal = normal.cross(tangent).normalized()
                vb.binormal.extend(struct.pack(
                    '<3B',
                    int(((-binormal[1] + 1.0) / 2) * 255),
                    int(((-binormal[2] + 1.0) / 2) * 255),
                    int(((-binormal[0] + 1.0) / 2) * 255)
                ))
                # vertex color light
                vb.color_hemi.append(int(round(hemi * 255, 0)))
                if vertex_color_sun:
                    vb.color_sun.append(int(round(sun * 255, 0)))
                    vb.color_light.extend(struct.pack(
                        '<3B',
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
                pw = rw.write.PackedWriter()
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
                packed_uv_fix = struct.pack(
                    '<2B',
                    tex_coord_u_correct,
                    tex_coord_v_correct
                )
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

        ib.extend((*face_indices[0], *face_indices[2], *face_indices[1]))

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


def write_tree_def_2(bpy_obj):
    packed_writer = rw.write.PackedWriter()

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
    scale_mat = utils.version.multiply(
        mathutils.Matrix.Scale(scale[0], 4, (1, 0, 0)),
        mathutils.Matrix.Scale(scale[1], 4, (0, 1, 0)),
        mathutils.Matrix.Scale(scale[2], 4, (0, 0, 1))
    )

    matrix = utils.version.multiply(
        location_mat, rotation_mat, scale_mat
    ).transposed()
    for row in matrix:
        packed_writer.putf('<4f', *row)
    write_ogf_color(packed_writer, bpy_obj, mode='SCALE')
    write_ogf_color(packed_writer, bpy_obj, mode='BIAS')

    return packed_writer


def write_fastpath_gcontainer(fastpath_obj, fp_vbs, fp_ibs, level):
    packed_writer = rw.write.PackedWriter()

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
            packed_co = struct.pack('<3f', vert.co[0], vert.co[2], vert.co[1])

            if unique_verts.get(packed_co, None) is None:
                unique_verts[packed_co] = vertex_index
                verts_indices[vert.index] = vertex_index
                vb.position.extend(packed_co)
                vb.vertex_count += 1
                vertices_count += 1
                vertex_index += 1
            else:
                duplicate_vertex_index = unique_verts[packed_co]
                verts_indices[vert.index] = duplicate_vertex_index

    for face in bm.faces:
        face_indices = []
        for vert in face.verts:
            vert_index = verts_indices[vert.index]
            packed_vert_index = struct.pack('<H', vert_index)
            face_indices.append(packed_vert_index)
            indices_count += 1

        ib.extend((*face_indices[0], *face_indices[2], *face_indices[1]))

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
    chunked_writer = rw.write.ChunkedWriter()
    writer = write_fastpath_gcontainer(fastpath_obj, fp_vbs, fp_ibs, level)
    chunked_writer.put(ogf.fmt.Chunks_v4.GCONTAINER, writer)
    return chunked_writer


def write_visual(
        bpy_obj,
        vbs,
        ibs,
        hierrarhy,
        visuals_ids,
        level,
        fp_vbs,
        fp_ibs
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
        chunked_writer = rw.write.ChunkedWriter()
        gcontainer_writer, visual = write_gcontainer(
            bpy_obj, vbs, ibs, level
        )
        if bpy_obj.xray.level.visual_type in ('TREE_ST', 'TREE_PM'):
            header_writer = write_visual_header(level, bpy_obj, visual=visual, visual_type=7)
            tree_def_2_writer = write_tree_def_2(bpy_obj)
            chunked_writer.put(ogf.fmt.HEADER, header_writer)
            chunked_writer.put(ogf.fmt.Chunks_v4.GCONTAINER, gcontainer_writer)
            chunked_writer.put(ogf.fmt.Chunks_v4.TREEDEF2, tree_def_2_writer)
        else:    # NORMAL or PROGRESSIVE visual
            header_writer = write_visual_header(level, bpy_obj, visual=visual)
            chunked_writer.put(ogf.fmt.HEADER, header_writer)
            chunked_writer.put(ogf.fmt.Chunks_v4.GCONTAINER, gcontainer_writer)
            if len(level.visuals_cache.children[bpy_obj.name]):
                raise log.AppError(
                    text.error.level_has_children,
                    log.props(object=bpy_obj.name)
                )
            if bpy_obj.xray.level.use_fastpath:
                fastpath_writer = write_fastpath(bpy_obj, fp_vbs, fp_ibs, level)
                chunked_writer.put(ogf.fmt.Chunks_v4.FASTPATH, fastpath_writer)
        return chunked_writer


def write_children_l(bpy_obj, hierrarhy, visuals_ids):
    packed_writer = rw.write.PackedWriter()
    packed_writer.putf('<I', len(hierrarhy[bpy_obj.name]))
    for child_obj in hierrarhy[bpy_obj.name]:
        child_index = visuals_ids[child_obj]
        packed_writer.putf('<I', child_index)
    return packed_writer


def write_hierrarhy_visual(bpy_obj, hierrarhy, visuals_ids, level):
    visual_writer = rw.write.ChunkedWriter()
    header_writer = write_visual_header(
        level,
        bpy_obj,
        visual_type=ogf.fmt.ModelType_v4.HIERRARHY,
        shader_id=0
    )
    visual_writer.put(ogf.fmt.HEADER, header_writer)
    children_l_writer = write_children_l(bpy_obj, hierrarhy, visuals_ids)
    visual_writer.put(ogf.fmt.Chunks_v4.CHILDREN_L, children_l_writer)
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


def write_lod_def_2(bpy_obj, level):
    packed_writer = rw.write.PackedWriter()
    me = bpy_obj.data
    material = bpy_obj.data.materials[0]
    uv_layer = me.uv_layers[material.xray.uv_texture]
    rgb_layer = me.vertex_colors[material.xray.light_vert_color]
    hemi_layer = me.vertex_colors[material.xray.hemi_vert_color]
    sun_layer = me.vertex_colors[material.xray.sun_vert_color]

    visual = Visual()
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
    visual_writer = rw.write.ChunkedWriter()

    children_l_writer = write_children_l(bpy_obj, hierrarhy, visuals_ids)
    lod_def_2_writer, visual = write_lod_def_2(bpy_obj, level)
    header_writer = write_visual_header(
        level, bpy_obj, visual=visual, visual_type=ogf.fmt.ModelType_v4.LOD
    )

    visual_writer.put(ogf.fmt.HEADER, header_writer)
    visual_writer.put(ogf.fmt.Chunks_v4.CHILDREN_L, children_l_writer)
    visual_writer.put(ogf.fmt.Chunks_v4.LODDEF2, lod_def_2_writer)

    return visual_writer


def write_visual_children(
        chunked_writer, vbs, ibs,
        visual_index, hierrarhy,
        visuals_ids, visuals, level, fp_vbs, fp_ibs
    ):

    for visual_obj in visuals:
        visual_chunked_writer = write_visual(
            visual_obj,
            vbs,
            ibs,
            hierrarhy,
            visuals_ids,
            level,
            fp_vbs,
            fp_ibs
        )
        if visual_chunked_writer:
            chunked_writer.put(visual_index, visual_chunked_writer)
            visual_index += 1
    return visual_index


def find_hierrarhy(level, visual_obj, visuals_hierrarhy, visual_index, visuals):
    visuals.append(visual_obj)
    visuals_hierrarhy[visual_obj.name] = []
    children_objs = []
    for child_obj_name in level.visuals_cache.children[visual_obj.name]:
        child_obj = bpy.data.objects[child_obj_name]
        children_objs.append(child_obj)
        visual_index += 1
        visuals_hierrarhy[visual_obj.name].append(child_obj)

    for child_child_obj in children_objs:
        if child_child_obj.xray.level.object_type == 'VISUAL':
            if child_child_obj.xray.level.visual_type != 'FASTPATH':
                visuals_hierrarhy, visual_index = find_hierrarhy(
                    level, child_child_obj, visuals_hierrarhy, visual_index, visuals
                )
    return visuals_hierrarhy, visual_index


def write_visuals(level_writer, level_object, sectors_portals, level):
    visuals_writer = rw.write.ChunkedWriter()
    sectors_chunked_writer = rw.write.ChunkedWriter()
    vertex_buffers = []
    indices_buffers = []
    fastpath_vertex_buffers = []
    fastpath_indices_buffers = []
    visual_index = 0
    sector_id = 0
    visuals_hierrarhy = {}
    visuals = []
    for child_obj_name in level.visuals_cache.children[level_object.name]:
        child_obj = bpy.data.objects[child_obj_name]
        if child_obj.name.startswith('sectors'):
            for sector_obj_name in level.visuals_cache.children[child_obj.name]:
                sector_obj = bpy.data.objects[sector_obj_name]
                for obj_name in level.visuals_cache.children[sector_obj.name]:
                    obj = bpy.data.objects[obj_name]
                    if obj.xray.level.object_type == 'VISUAL':
                        visuals_hierrarhy, visual_index = find_hierrarhy(
                            level, obj, visuals_hierrarhy, visual_index, visuals
                        )
                        visual_index += 1
    visuals.reverse()
    visuals_ids = {}
    for visual_index, visual_obj in enumerate(visuals):
        visuals_ids[visual_obj] = visual_index
    visual_index = 0

    for child_obj_name in level.visuals_cache.children[level_object.name]:
        child_obj = bpy.data.objects[child_obj_name]
        if child_obj.name.startswith('sectors'):
            for sector_obj_name in level.visuals_cache.children[child_obj.name]:
                sector_obj = bpy.data.objects[sector_obj_name]
                level.sectors_indices[sector_obj.name] = sector_id
                cform_obj = None

                for root_obj_name in level.visuals_cache.children[sector_obj.name]:
                    root_obj = bpy.data.objects[root_obj_name]
                    if root_obj.xray.level.object_type == 'VISUAL':
                        # write sector
                        root_index = visuals_ids[root_obj]
                        sector_chunked_writer = write_sector(
                            root_index,
                            sectors_portals,
                            sector_obj.name
                        )
                        sectors_chunked_writer.put(sector_id, sector_chunked_writer)
                    elif root_obj.xray.level.object_type == 'CFORM':
                        cform_obj = root_obj
                        level.cform_objects[sector_id] = cform_obj

                # check cform-object
                if not cform_obj:
                    raise log.AppError(
                        text.error.level_sector_has_no_cform,
                        log.props(sector_object=sector_obj.name)
                    )
                if cform_obj.type != 'MESH':
                    raise log.AppError(
                        text.error.level_bad_cform_type,
                        log.props(
                            object=cform_obj.name,
                            type=cform_obj.type
                        )
                    )
                if not len(cform_obj.data.polygons):
                    raise log.AppError(
                        text.error.level_cform_no_geom,
                        log.props(object=cform_obj.name)
                    )
                if not len(cform_obj.data.materials):
                    raise log.AppError(
                        text.error.level_cform_no_mats,
                        log.props(object=cform_obj.name)
                    )

                sector_id += 1

    visual_index = write_visual_children(
        visuals_writer, vertex_buffers, indices_buffers,
        visual_index, visuals_hierrarhy, visuals_ids, visuals, level,
        fastpath_vertex_buffers, fastpath_indices_buffers
    )

    level_writer.put(fmt.Chunks13.VISUALS, visuals_writer)

    return (
        vertex_buffers, indices_buffers,
        fastpath_vertex_buffers, fastpath_indices_buffers,
        sectors_chunked_writer
    )


def write_glow(glows_writer, glow_obj, level):
    # position
    glows_writer.putf(
        '<3f',
        glow_obj.location[0],
        glow_obj.location[2],
        glow_obj.location[1]
    )
    faces_count = len(glow_obj.data.polygons)
    if not faces_count:
        raise log.AppError(
            text.error.level_bad_glow,
            log.props(
                object=glow_obj.name,
                faces_count=faces_count
            )
        )
    dim_max = max(glow_obj.dimensions)
    glow_radius = dim_max / 2
    if glow_radius < 0.0005:
        raise log.AppError(
            text.error.level_bad_glow_radius,
            log.props(
                object=glow_obj.name,
                radius=glow_radius
            )
        )
    glows_writer.putf('<f', glow_radius)
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
    glows_writer.putf('<H', shader_index + 1)


def write_glows(level_writer, level_object, level):
    glows_writer = rw.write.PackedWriter()
    for child_obj_name in level.visuals_cache.children[level_object.name]:
        child_obj = bpy.data.objects[child_obj_name]
        if child_obj.name.startswith('glows'):
            for glow_obj_name in level.visuals_cache.children[child_obj.name]:
                glow_obj = bpy.data.objects[glow_obj_name]
                write_glow(glows_writer, glow_obj, level)
    level_writer.put(fmt.Chunks13.GLOWS, glows_writer)


def write_light(level_writer, level, level_object):
    light_writer = rw.write.PackedWriter()
    for child_obj_name in level.visuals_cache.children[level_object.name]:
        child_obj = bpy.data.objects[child_obj_name]
        if child_obj.name.startswith('light dynamic'):
            for light_obj_name in level.visuals_cache.children[child_obj.name]:
                light_obj = bpy.data.objects[light_obj_name]
                data = light_obj.xray.level
                controller_id = data.controller_id
                if controller_id == -1:
                    controller_id = 2 ** 32
                light_writer.putf('<I', controller_id)
                light_writer.putf('<I', data.light_type)
                light_writer.putf('<4f', *data.diffuse)
                light_writer.putf('<4f', *data.specular)
                light_writer.putf('<4f', *data.ambient)
                light_writer.putf(
                    '<3f',
                    light_obj.location[0],
                    light_obj.location[2],
                    light_obj.location[1]
                )
                euler = light_obj.matrix_world.to_euler('YXZ')
                matrix = euler.to_matrix().to_3x3()
                direction = (matrix[0][1], matrix[2][1], matrix[1][1])
                light_writer.putf('<3f', direction[0], direction[1], direction[2])
                light_writer.putf('<f', data.range_)
                light_writer.putf('<f', data.falloff)
                light_writer.putf('<f', data.attenuation_0)
                light_writer.putf('<f', data.attenuation_1)
                light_writer.putf('<f', data.attenuation_2)
                light_writer.putf('<f', data.theta)
                light_writer.putf('<f', data.phi)
    level_writer.put(fmt.Chunks13.LIGHT_DYNAMIC, light_writer)


def write_portals(level_writer, level, level_object):
    portals_writer = rw.write.PackedWriter()

    for child_name in level.visuals_cache.children[level_object.name]:
        child_obj = bpy.data.objects[child_name]

        if child_obj.name.startswith('portals'):
            portals_objs = level.visuals_cache.children[child_obj.name]

            for portal_index, portal_name in enumerate(portals_objs):
                portal_obj = bpy.data.objects[portal_name]
                xray = portal_obj.xray

                if xray.level.object_type != 'PORTAL':
                    continue

                if portal_obj.type != 'MESH':
                    raise log.AppError(
                        text.error.level_portal_is_no_mesh,
                        log.props(
                            portal_object=portal_obj.name,
                            object_type=portal_obj.type
                        )
                    )

                portal_mesh = portal_obj.data
                verts_count = len(portal_mesh.vertices)
                faces_count = len(portal_mesh.polygons)
                error_message = None

                # check vertices
                if not verts_count:
                    error_message = text.error.level_portal_no_vert
                elif verts_count < 3:
                    error_message = text.error.level_portal_bad
                elif verts_count > 6:
                    error_message = text.error.level_portal_many_verts

                if error_message:
                    raise log.AppError(
                        error_message,
                        log.props(
                            portal_object=portal_obj.name,
                            vertices_count=verts_count
                        )
                    )

                # check polygons
                if not faces_count:
                    error_message = text.error.level_portal_no_faces
                elif faces_count > 1:
                    error_message = text.error.level_portal_many_faces

                if error_message:
                    raise log.AppError(
                        error_message,
                        log.props(
                            portal_object=portal_obj.name,
                            polygons_count=faces_count
                        )
                    )

                # write portal sectors
                if xray.level.sector_front:
                    sect_front = level.sectors_indices[xray.level.sector_front]
                else:
                    raise log.AppError(
                        text.error.level_portal_no_front,
                        log.props(portal_object=portal_obj.name)
                    )

                if xray.level.sector_back:
                    sect_back = level.sectors_indices[xray.level.sector_back]
                else:
                    raise log.AppError(
                        text.error.level_portal_no_back,
                        log.props(portal_object=portal_obj.name)
                    )

                portals_writer.putf('<2H', sect_front, sect_back)

                # write vertices
                for vert_index in portal_mesh.polygons[0].vertices:
                    vert = portal_mesh.vertices[vert_index]
                    portals_writer.putf('<3f', vert.co.x, vert.co.z, vert.co.y)

                # write not used vertices
                verts_count = len(portal_mesh.vertices)
                for vert_index in range(verts_count, fmt.PORTAL_VERTEX_COUNT):
                    portals_writer.putf('<3f', 0.0, 0.0, 0.0)

                portals_writer.putf('<I', verts_count)

    level_writer.put(fmt.Chunks13.PORTALS, portals_writer)


def append_portal(sectors_portals, sector_index, portal_index):
    sectors_portals.setdefault(sector_index, []).append(portal_index)


def get_sectors_portals(level, level_object):
    sectors_portals = {}

    for obj_name in level.visuals_cache.children[level_object.name]:
        obj = bpy.data.objects[obj_name]
        if obj.name.startswith('portals'):
            portal_objs = level.visuals_cache.children[obj.name]

            for portal_index, portal_name in enumerate(portal_objs):
                portal_obj = bpy.data.objects[portal_name]

                append_portal(
                    sectors_portals,
                    portal_obj.xray.level.sector_front,
                    portal_index
                )
                append_portal(
                    sectors_portals,
                    portal_obj.xray.level.sector_back,
                    portal_index
                )

    return sectors_portals


def write_header(geom_writer):
    header_writer = rw.write.PackedWriter()

    header_writer.putf('<H', fmt.VERSION_14)
    header_writer.putf('<H', 0)    # quality

    geom_writer.put(fmt.HEADER, header_writer)


def write_level(file_path, level_object):
    level = Level()
    level_folder = utils.version.get_preferences().levels_folder_auto
    level.source_level_path = os.path.join(level_folder, level_object.name)
    level_writer = get_writer()

    # header
    write_header(level_writer)

    sectors_portals = get_sectors_portals(level, level_object)

    # visuals
    (
        vbs, ibs,
        vbs_fp, ibs_fp,
        sectors_writer
    ) = write_visuals(level_writer, level_object, sectors_portals, level)

    # portals
    write_portals(level_writer, level, level_object)

    # lights
    write_light(level_writer, level, level_object)

    # glows
    write_glows(level_writer, level_object, level)

    # shaders
    write_shaders(level_writer, level)

    # sectors
    level_writer.put(fmt.Chunks13.SECTORS, sectors_writer)

    # save level file
    rw.utils.save_file(file_path, level_writer)

    return vbs, ibs, vbs_fp, ibs_fp, level


def get_bbox(bbox_1, bbox_2, function):
    if not bbox_1:
        return bbox_2
    bbox_x = function(bbox_1[0], bbox_2[0])
    bbox_y = function(bbox_1[1], bbox_2[1])
    bbox_z = function(bbox_1[2], bbox_2[2])
    return (bbox_x, bbox_y, bbox_z)


def write_cform(file_path, level):
    materials = set()
    bbox_min = None
    bbox_max = None

    for cform_object in level.cform_objects.values():
        # find min/max bbox
        bbox_min = get_bbox(bbox_min, cform_object.bound_box[0], min)
        bbox_max = get_bbox(bbox_max, cform_object.bound_box[6], max)
        # collect materials
        for material in cform_object.data.materials:
            if material:
                materials.add(material)

    # get gamemtl.xr data
    pref = utils.version.get_preferences()
    gamemtl_file = pref.gamemtl_file_auto
    if os.path.exists(gamemtl_file):
        gamemtl_data = rw.utils.read_file(gamemtl_file)
    else:
        gamemtl_data = None

    # read gamemtl.xr
    gamemtl_ids = {}
    if gamemtl_data:
        for gamemtl_name, _, gamemtl_id in xr.parse_gamemtl(gamemtl_data):
            gamemtl_ids[gamemtl_name] = gamemtl_id

    # find game material ids
    game_materials = {}
    for material in materials:
        gamemtl = material.xray.gamemtl
        gamemtl_id = gamemtl_ids.get(gamemtl, None)
        # game material id by gamemtl name
        if gamemtl_id is None:
            if gamemtl.isdigit():
                gamemtl_id = int(gamemtl)
        # game material id by material name
        if gamemtl_id is None:
            prefix = material.name.split('_')[0]
            if prefix.isdigit():
                gamemtl_id = int(prefix)
            else:
                gamemtl_id = 0
        game_materials[material.name] = gamemtl_id

    # write geometry
    tris_count = 0
    verts_count = 0

    verts_writer = rw.write.PackedWriter()
    tris_writer = rw.write.PackedWriter()

    sectors_count = len(level.cform_objects)

    for sector_index in range(sectors_count):
        cform_object = level.cform_objects[sector_index]

        # create bmesh and triangulate
        bm = bmesh.new()
        bm.from_mesh(cform_object.data)
        bmesh.ops.triangulate(bm, faces=bm.faces)

        # write vertices
        for vert in bm.verts:
            verts_writer.putf('<3f', vert.co.x, vert.co.z, vert.co.y)

        # write triangles
        for face in bm.faces:

            # write vertex indices
            vert_1, vert_2, vert_3 = face.verts
            tris_writer.putf(
                '<3I',
                vert_1.index + verts_count,
                vert_3.index + verts_count,
                vert_2.index + verts_count
            )

            # write material and sector
            mat = cform_object.data.materials[face.material_index]
            if not mat:
                raise log.AppError(
                    text.error.level_cform_empty_mat_slot,
                    log.props(
                        cform_object=cform_object.name,
                        material_slot_index=face.material_index
                    )
                )
            material_id = game_materials[mat.name]
            suppress_shadows = (int(mat.xray.suppress_shadows) << 14) & 0x4000
            suppress_wm = (int(mat.xray.suppress_wm) << 15) & 0x8000
            tris_attributes = material_id | suppress_shadows | suppress_wm
            tris_writer.putf('<2H', tris_attributes, sector_index)

        verts_count += len(bm.verts)
        tris_count += len(bm.faces)

    # write header
    header_writer = rw.write.PackedWriter()
    header_writer.putf('<I', fmt.CFORM_VERSION_4)
    header_writer.putf('<I', verts_count)
    header_writer.putf('<I', tris_count)
    header_writer.putf('<3f', bbox_min[0], bbox_min[2], bbox_min[1])
    header_writer.putf('<3f', bbox_max[0], bbox_max[2], bbox_max[1])

    # write cform
    cform_writer = rw.write.PackedWriter()
    cform_writer.putp(header_writer)
    cform_writer.putp(verts_writer)
    cform_writer.putp(tris_writer)

    # save file
    cform_path = file_path + os.extsep + 'cform'
    rw.utils.save_file(cform_path, cform_writer)


def get_writer():
    chunked_writer = rw.write.ChunkedWriter()
    return chunked_writer


@log.with_context(name='export-game-level')
def export_file(level_object, dir_path):
    log.update(object=level_object.name)

    file_path = os.path.join(dir_path, 'level')

    # write level file
    vbs, ibs, fp_vbs, fp_ibs, level = write_level(file_path, level_object)

    # write level.geom file
    write_geom(file_path, vbs, ibs, 'geom')

    # write level.geomx file
    write_geom(file_path, fp_vbs, fp_ibs, 'geomx')

    # write level.cform file
    write_cform(file_path, level)
