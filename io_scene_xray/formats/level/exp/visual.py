# standart modules
import math
import struct

# blender modules
import bpy
import bmesh
import mathutils

# addon modules
from . import shader
from . import sector
from . import types
from .. import fmt
from ... import ogf
from .... import text
from .... import utils
from .... import log
from .... import rw


TWO_MEGABYTES = 1024 * 1024 * 2
MAX_TILE = 16
QUANT = 32768 / MAX_TILE


def write_visual_bounding_sphere(header_writer, center, radius):
    header_writer.putf('<3f', center[0], center[2], center[1])
    header_writer.putf('<f', radius)


def write_visual_bounding_box(header_writer, bbox):
    bbox_min = bbox[0]
    bbox_max = bbox[1]
    header_writer.putf('<3f', bbox_min[0], bbox_min[2], bbox_min[1])    # min
    header_writer.putf('<3f', bbox_max[0], bbox_max[2], bbox_max[1])    # max


def write_visual_header(
        level,
        bpy_obj,
        visual=None,
        visual_type=0,
        shader_id=0
    ):

    header_writer = rw.write.PackedWriter()
    header_writer.putf('<B', ogf.fmt.FORMAT_VERSION_4)
    header_writer.putf('<B', visual_type)

    if visual:
        # +1 - skip first empty shader
        header_writer.putf('<H', visual.shader_index + 1)
    else:
        header_writer.putf('<H', shader_id)    # shader id

    bbox, (center, radius) = utils.mesh.calculate_bbox_and_bsphere(
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

    # clamp uv
    if coord_h > 0x7fff:
        coord_h = 0x7fff
    elif coord_h < -0x8000:
        coord_h = -0x8000

    return int(round(tex_correct, 0)), coord_h


def write_gcontainer(bpy_obj, vbs, ibs, level):
    if bpy_obj.type != 'MESH':
        raise log.AppError(
            text.error.level_visual_is_not_mesh,
            log.props(
                object=bpy_obj.name,
                type=bpy_obj.type,
                visual_type=bpy_obj.xray.level.visual_type
            )
        )

    bpy_mesh = bpy_obj.data
    faces_count = len(bpy_mesh.polygons)

    if not faces_count:
        raise log.AppError(
            text.error.level_visual_no_faces,
            log.props(object=bpy_obj.name)
        )

    material, shader_index = shader.get_shader_index(
        level,
        bpy_obj,
        text.error.level_visual_no_mat,
        text.error.level_visual_many_mats,
        text.error.level_visual_empty_mat
    )

    visual = types.Visual()
    visual.shader_index = shader_index

    packed_writer = rw.write.PackedWriter()

    # multiple usage visuals
    gcontainer = level.saved_visuals.get(bpy_mesh.name, None)
    if gcontainer:
        packed_writer.putf('<I', gcontainer[0])    # vb_index
        packed_writer.putf('<I', gcontainer[1])    # vb_offset
        packed_writer.putf('<I', gcontainer[2])    # vb_size

        packed_writer.putf('<I', gcontainer[3])    # ib_index
        packed_writer.putf('<I', gcontainer[4])    # ib_offset
        packed_writer.putf('<I', gcontainer[5])    # ib_size

        return packed_writer, visual

    bm = bmesh.new()
    bm.from_mesh(bpy_mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    export_mesh = bpy.data.meshes.new('temp_mesh')
    export_mesh.use_auto_smooth = True
    export_mesh.auto_smooth_angle = math.pi
    bm.to_mesh(export_mesh)
    export_mesh.calc_normals_split()

    uv_layer = bm.loops.layers.uv.get(material.xray.uv_texture)

    if not uv_layer:
        raise log.AppError(
            text.error.level_visual_no_uv,
            log.props(
                object=bpy_obj.name,
                uv=material.xray.uv_texture
            )
        )

    uv_layer_lmap = bm.loops.layers.uv.get(material.xray.uv_light_map, None)
    color_sun = bm.loops.layers.color.get(material.xray.sun_vert_color, None)
    vertex_color_hemi = bm.loops.layers.color.get(
        material.xray.hemi_vert_color, None
    )
    color_light = bm.loops.layers.color.get(
        material.xray.light_vert_color, None
    )
    export_mesh.calc_tangents(uvmap=uv_layer.name)

    vertex_size = 32
    if color_sun:
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
                if vertex_buffer.vertex_count * vertex_size > TWO_MEGABYTES:
                    # vertex buffer should not be more than 2 MB
                    continue
                else:
                    vb = vertex_buffer
                    break
        if vb is None:
            vb = types.VertexBuffer()
            vb.vertex_format = vertex_format
            vbs.append(vb)
            level.vbs_offsets.append(0)
    else:
        vb = types.VertexBuffer()
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
    lmap_uvs = []
    hemies = []
    suns = []
    lights = []

    for face in bm.faces:
        for loop in face.loops:
            vert = loop.vert
            vert_co = (vert.co[0], vert.co[1], vert.co[2])
            split_normal = export_mesh.loops[loop.index].normal
            normal = (split_normal[0], split_normal[1], split_normal[2])
            uv = loop[uv_layer].uv[0], loop[uv_layer].uv[1]

            # light map uv
            if uv_layer_lmap:
                uv_lmap = loop[uv_layer_lmap].uv[0], loop[uv_layer_lmap].uv[1]
            else:
                uv_lmap = None
            lmap_uvs.append(uv_lmap)

            # hemi
            if vertex_color_hemi:
                hemi = loop[vertex_color_hemi][0]
            else:
                hemi = None
            hemies.append(hemi)

            # sun
            if color_sun:
                sun = loop[color_sun][0]
            else:
                sun = None
            suns.append(sun)

            # light
            if color_light:
                light = loop[color_light]
            else:
                light = None
            lights.append(light)

            vert_key = (uv, uv_lmap, normal, hemi, sun, light)
            if unique_verts.get(vert_co, None) is None:
                unique_verts[vert_co] = [vert_key, ]
                verts_indices[vert_co] = [vertex_index, ]
                vertex_index += 1
            else:
                if not vert_key in unique_verts[vert_co]:
                    unique_verts[vert_co].append(vert_key)
                    verts_indices[vert_co].append(vertex_index)
                    vertex_index += 1

    saved_verts = set()
    if uv_layer_lmap or color_sun:
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
            vert_key = tuple(vert.co)
            vert_data = unique_verts[vert_key]
            uv = tuple(loop[uv_layer].uv)
            split_normal = tuple(export_mesh.loops[loop.index].normal)

            # light map uv
            uv_lmap = lmap_uvs[loop.index]

            # vertex color hemi
            hemi = hemies[loop.index]

            # vertex color sun
            sun = suns[loop.index]

            # vertex color light
            light = lights[loop.index]

            for index, data in enumerate(vert_data):
                if (
                        data[0] == uv and
                        data[1] == uv_lmap and
                        data[2] == split_normal and
                        data[3] == hemi and
                        data[4] == sun and
                        data[5] == light
                    ):
                    tex_uv, tex_uv_lmap, normal, hemi, sun, light = data
                    vert_index = verts_indices[vert_key][index]
                    break

            packed_vertex_index = struct.pack('<H', vert_index)
            face_indices.append(packed_vertex_index)
            indices_count += 1

            if not vert_index in saved_verts:
                saved_verts.add(vert_index)
                vb.vertex_count += 1
                vertices_count += 1

                # position
                vb.position.extend(
                    struct.pack('<3f', vert.co[0], vert.co[2], vert.co[1])
                )

                # normal
                vb.normal.extend(struct.pack(
                    '<3B',
                    int(((normal[1] + 1.0) / 2) * 255),
                    int(((normal[2] + 1.0) / 2) * 255),
                    int(((normal[0] + 1.0) / 2) * 255)
                ))

                # tangent
                tangent = export_mesh.loops[loop.index].tangent
                vb.tangent.extend(struct.pack(
                    '<3B',
                    int(((tangent[1] + 1.0) / 2) * 255),
                    int(((tangent[2] + 1.0) / 2) * 255),
                    int(((tangent[0] + 1.0) / 2) * 255)
                ))

                # binormal
                binorm = mathutils.Vector(normal).cross(tangent).normalized()
                vb.binormal.extend(struct.pack(
                    '<3B',
                    int(((-binorm[1] + 1.0) / 2) * 255),
                    int(((-binorm[2] + 1.0) / 2) * 255),
                    int(((-binorm[0] + 1.0) / 2) * 255)
                ))

                # hemi
                vb.color_hemi.append(int(round(hemi * 255, 0)))

                # sun
                if color_sun:
                    vb.color_sun.append(int(round(sun * 255, 0)))

                    # light
                    vb.color_light.extend(struct.pack(
                        '<3B',
                        (int(round(light[2] * 255, 0))),
                        (int(round(light[1] * 255, 0))),
                        (int(round(light[0] * 255, 0)))
                    ))

                # uv
                coord_u = int(tex_uv[0] * uv_coeff)
                coord_v = int((1.0 - tex_uv[1]) * uv_coeff)

                # uv corrector
                correct_u, coord_u = get_tex_coord_correct(
                    tex_uv[0],
                    coord_u,
                    uv_coeff
                )
                correct_v, coord_v = get_tex_coord_correct(
                    1 - tex_uv[1],
                    coord_v,
                    uv_coeff
                )

                # write uv
                vb.uv.extend(struct.pack('<2h', coord_u, coord_v))

                # write uv corrector
                vb.uv_fix.extend(struct.pack('<2B', correct_u, correct_v))

                if uv_layer_lmap:
                    lmap_u = int(round(
                        tex_uv_lmap[0] * fmt.LIGHT_MAP_UV_COEFFICIENT,
                        0
                    ))
                    lmap_v = int(round((
                        1 - tex_uv_lmap[1]) * fmt.LIGHT_MAP_UV_COEFFICIENT,
                        0
                    ))
                    vb.uv_lmap.extend(struct.pack('<2h', lmap_u, lmap_v))

                # tree shader data (wind coefficient)
                if not (uv_layer_lmap or color_sun or color_light):
                    f1 = (vert.co[2] - frac_low[2]) / frac_y_size
                    f2 = find_distance(vert.co, frac_low) / frac_y_size
                    frac = quant_value((f1 + f2) / 2)    # wind coefficient
                    vb.shader_data.extend(struct.pack('<H', frac))

        ib.extend((*face_indices[0], *face_indices[2], *face_indices[1]))

    vertex_buffer_index = vbs.index(vb)

    # vb_index
    packed_writer.putf('<I', vertex_buffer_index)
    # vb_offset
    packed_writer.putf('<I', level.vbs_offsets[vertex_buffer_index])
    # vb_size
    packed_writer.putf('<I', vertices_count)

    # ib_index
    packed_writer.putf('<I', indices_buffer_index)
    # ib_offset
    packed_writer.putf('<I', ib_offset)
    # ib_size
    packed_writer.putf('<I', indices_count)

    level.saved_visuals[bpy_mesh.name] = (
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
                if vertex_buffer.vertex_count * vertex_size > TWO_MEGABYTES:
                    continue
                else:
                    vb = vertex_buffer
                    break
        if vb is None:
            vb = types.VertexBuffer()
            vb.vertex_format = vertex_format
            fp_vbs.append(vb)
            level.fp_vbs_offsets.append(0)
    else:
        vb = types.VertexBuffer()
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

    # vb_index
    packed_writer.putf('<I', vertex_buffer_index)
    # vb_offset
    packed_writer.putf('<I', level.fp_vbs_offsets[vertex_buffer_index])
    # vb_size
    packed_writer.putf('<I', vertices_count)

    # ib_index
    packed_writer.putf('<I', indices_buffer_index)
    # ib_offset
    packed_writer.putf('<I', ib_offset)
    # ib_size
    packed_writer.putf('<I', indices_count)

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

    level_props = bpy_obj.xray.level

    if level_props.visual_type == 'HIERRARHY':
        visual_writer = write_hierrarhy_visual(
            bpy_obj,
            hierrarhy,
            visuals_ids,
            level
        )

    elif level_props.visual_type == 'LOD':
        visual_writer = write_lod_visual(
            bpy_obj,
            hierrarhy,
            visuals_ids,
            level
        )

    else:
        visual_writer = rw.write.ChunkedWriter()
        gcontainer_writer, visual = write_gcontainer(
            bpy_obj,
            vbs,
            ibs,
            level
        )

        if level_props.visual_type in ('TREE_ST', 'TREE_PM'):
            header_writer = write_visual_header(
                level,
                bpy_obj,
                visual=visual,
                visual_type=7
            )
            tree_def_2_writer = write_tree_def_2(bpy_obj)
            visual_writer.put(ogf.fmt.HEADER, header_writer)
            visual_writer.put(ogf.fmt.Chunks_v4.GCONTAINER, gcontainer_writer)
            visual_writer.put(ogf.fmt.Chunks_v4.TREEDEF2, tree_def_2_writer)

        else:    # NORMAL or PROGRESSIVE visual
            header_writer = write_visual_header(level, bpy_obj, visual=visual)
            visual_writer.put(ogf.fmt.HEADER, header_writer)
            visual_writer.put(ogf.fmt.Chunks_v4.GCONTAINER, gcontainer_writer)
            if len(level.visuals_cache.children[bpy_obj.name]):
                raise log.AppError(
                    text.error.level_has_children,
                    log.props(object=bpy_obj.name)
                )
            if level_props.use_fastpath:
                fp_writer = write_fastpath(bpy_obj, fp_vbs, fp_ibs, level)
                visual_writer.put(ogf.fmt.Chunks_v4.FASTPATH, fp_writer)

    return visual_writer


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

    visual = types.Visual()
    if level.materials.get(material, None) is None:
        level.materials[material] = level.active_material_index
        visual.shader_index = level.active_material_index
        level.active_material_index += 1
    else:
        visual.shader_index = level.materials[material]

    if len(me.polygons) != 8:
        raise BaseException(
            'LOD mesh "{}" has not 8 polygons'.format(bpy_obj.data)
        )

    if len(me.vertices) != 32:
        raise BaseException(
            'LOD mesh "{}"  has not 32 vertices'.format(bpy_obj.data)
        )

    for face_index in range(8):
        face = me.polygons[face_index]
        for face_vertex_index in range(4):
            vert_index = face.vertices[face_vertex_index]
            vert = me.vertices[vert_index]
            packed_writer.putf('<3f', vert.co.x, vert.co.z, vert.co.y)
            loop_index = face.loop_indices[face_vertex_index]
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
            # fill with bytes so that the size of the
            # structure is a multiple of 4
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
        chunked_writer,
        vbs,
        ibs,
        hierrarhy,
        visuals_ids,
        visuals,
        level,
        fp_vbs,
        fp_ibs
    ):

    visual_index = 0

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


def find_hierrarhy(
        level,
        visual_obj,
        visuals_hierrarhy,
        visual_index,
        visuals
    ):

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
                    level,
                    child_child_obj,
                    visuals_hierrarhy,
                    visual_index,
                    visuals
                )

    return visuals_hierrarhy, visual_index


def write_visuals(level_writer, level_object, level):
    visuals_writer = rw.write.ChunkedWriter()
    sectors_writer = rw.write.ChunkedWriter()
    vertex_buffers = []
    indices_buffers = []
    fastpath_vertex_buffers = []
    fastpath_indices_buffers = []
    visual_index = 0
    sector_id = 0
    visuals_hierrarhy = {}
    visuals = []
    children = level.visuals_cache.children

    for child_obj_name in children[level_object.name]:
        child_obj = bpy.data.objects[child_obj_name]
        if child_obj.name.startswith('sectors'):
            for sector_obj_name in children[child_obj.name]:
                sector_obj = bpy.data.objects[sector_obj_name]
                for obj_name in children[sector_obj.name]:
                    obj = bpy.data.objects[obj_name]
                    if obj.xray.level.object_type == 'VISUAL':
                        visuals_hierrarhy, visual_index = find_hierrarhy(
                            level,
                            obj,
                            visuals_hierrarhy,
                            visual_index,
                            visuals
                        )
                        visual_index += 1

    visuals.reverse()
    visuals_ids = {}
    for visual_index, visual_obj in enumerate(visuals):
        visuals_ids[visual_obj] = visual_index

    sectors_portals = sector.get_sectors_portals(level, level_object)

    for child_obj_name in children[level_object.name]:
        child_obj = bpy.data.objects[child_obj_name]
        if child_obj.name.startswith('sectors'):
            for sector_obj_name in children[child_obj.name]:
                sector_obj = bpy.data.objects[sector_obj_name]
                level.sectors_indices[sector_obj.name] = sector_id
                cform_obj = None

                for root_obj_name in children[sector_obj.name]:
                    root_obj = bpy.data.objects[root_obj_name]
                    if root_obj.xray.level.object_type == 'VISUAL':
                        # write sector
                        root_index = visuals_ids[root_obj]
                        sector_chunked_writer = sector.write_sector(
                            root_index,
                            sectors_portals,
                            sector_obj.name
                        )
                        sectors_writer.put(sector_id, sector_chunked_writer)
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

    visual_index = 0
    write_visual_children(
        visuals_writer,
        vertex_buffers,
        indices_buffers,
        visuals_hierrarhy,
        visuals_ids,
        visuals,
        level,
        fastpath_vertex_buffers,
        fastpath_indices_buffers
    )

    level_writer.put(fmt.Chunks13.VISUALS, visuals_writer)

    return (
        vertex_buffers,
        indices_buffers,
        fastpath_vertex_buffers,
        fastpath_indices_buffers,
        sectors_writer
    )
