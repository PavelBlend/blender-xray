import math

import bpy, mathutils, bmesh

from .. import xray_io
from ..level import (
    swi as imp_swi, create as level_create, shaders as level_shaders,
    fmt as level_fmt, vb as level_vb
)
from . import fmt


class Visual(object):
    def __init__(self):
        self.visual_id = None
        self.format_version = None
        self.model_type = None
        self.shader_id = None
        self.texture_id = None
        self.name = None
        self.vertices = None
        self.uvs = None
        self.uvs_lmap = None
        self.triangles = None
        self.indices_count = None
        self.indices = None
        self.hemi = None
        self.sun = None
        self.light = None
        self.fastpath = False
        self.use_two_sided_tris = False
        self.vb_index = None


class HierrarhyVisual(object):
    def __init__(self):
        self.index = None
        self.children = []
        self.children_count = None


def get_material(level, shader_id, texture_id):
    material_key = (shader_id, texture_id)
    bpy_material = level.materials[shader_id]
    if not bpy_material:
        if not (level.shaders and level.textures):
            shader_raw = level.shaders_or_textures[shader_id]
            texture_raw = level.shaders_or_textures[texture_id]
            shader_data = shader_raw + '/' + texture_raw
            bpy_material = level_shaders.import_shader(
                level, level.context, shader_data
            )
        else:
            shader_raw = level.shaders[shader_id]
            texture_raw = level.textures[texture_id]
            shader_data = shader_raw + '/' + texture_raw
            bpy_material = level_shaders.import_shader(
                level, level.context, shader_data
            )
    level.materials[material_key] = bpy_material
    return bpy_material


def assign_material(bpy_object, visual, level):
    if (
            visual.format_version == fmt.FORMAT_VERSION_4 or
            level.xrlc_version >= level_fmt.VERSION_12
        ):
        shader_id = visual.shader_id
        bpy_material = level.materials[shader_id]
        if visual.use_two_sided_tris:
            bpy_material.xray.flags_twosided = True
    else:
        bpy_material = get_material(level, visual.shader_id, visual.texture_id)
    bpy_object.data.materials.append(bpy_material)


def create_object(name, obj_data):
    bpy_object = bpy.data.objects.new(name, obj_data)
    bpy.context.scene.collection.objects.link(bpy_object)
    return bpy_object


def convert_normal(norm_in):
    norm_out_x = 2.0 * norm_in[0] / 255 - 1.0
    norm_out_y = 2.0 * norm_in[1] / 255 - 1.0
    norm_out_z = 2.0 * norm_in[2] / 255 - 1.0
    return mathutils.Vector((norm_out_z, norm_out_x, norm_out_y)).normalized()


def convert_float_normal(norm_in):
    return mathutils.Vector((norm_in[2], norm_in[0], norm_in[1])).normalized()


def create_visual(bpy_mesh, visual, level, geometry_key):
    if not bpy_mesh:
        mesh = bmesh.new()

        temp_mesh = bmesh.new()

        remap_vertex_index = 0
        remap_vertices = {}
        unique_verts = {}
        vert_normals = {}
        for vertex_index, vertex_coord in enumerate(visual.vertices):
            vert = temp_mesh.verts.new(vertex_coord)
            vert_normals[tuple(vert.co)] = []

        temp_mesh.verts.ensure_lookup_table()
        temp_mesh.verts.index_update()

        for triangle in visual.triangles:
            temp_mesh.faces.new((
                temp_mesh.verts[triangle[0]],
                temp_mesh.verts[triangle[1]],
                temp_mesh.verts[triangle[2]]
            ))

        temp_mesh.faces.ensure_lookup_table()
        temp_mesh.normal_update()

        back_side = {}

        for vert in temp_mesh.verts:
            norm = (
                round(vert.normal[0], 3),
                round(vert.normal[1], 3),
                round(vert.normal[2], 3)
            )
            vert_normals[tuple(vert.co)].append((vert.index, norm))

        temp_mesh.clear()
        del temp_mesh

        for vertex_co, norms in vert_normals.items():
            back_side_norms = set()
            for vertex_index, normal in norms:
                normal = tuple(normal)
                back_norm = (-normal[0], -normal[1], -normal[2])
                if back_norm in back_side_norms:
                    back_side[vertex_index] = True
                else:
                    back_side[vertex_index] = False
                    back_side_norms.add(normal)

        # import vertices
        remap_vertex_index = 0
        remap_vertices = {}
        unique_verts = {}
        for vertex_index, vertex_coord in enumerate(visual.vertices):
            is_back_vert = back_side[vertex_index]
            if unique_verts.get((vertex_coord, is_back_vert), None) is None:
                mesh.verts.new(vertex_coord)
                remap_vertices[vertex_index] = remap_vertex_index
                unique_verts[(vertex_coord, is_back_vert)] = remap_vertex_index
                remap_vertex_index += 1
            else:
                current_remap_vertex_index = unique_verts[(vertex_coord, is_back_vert)]
                remap_vertices[vertex_index] = current_remap_vertex_index

        mesh.verts.ensure_lookup_table()
        mesh.verts.index_update()

        # import triangles
        remap_loops = []
        custom_normals = []
        if not visual.vb_index is None:
            if not level.vertex_buffers[visual.vb_index].float_normals:
                convert_normal_function = convert_normal
        else:
            convert_normal_function = convert_float_normal
        if level.xrlc_version >= level_fmt.VERSION_11:
            for triangle in visual.triangles:
                try:
                    vert_1 = remap_vertices[triangle[0]]
                    vert_2 = remap_vertices[triangle[1]]
                    vert_3 = remap_vertices[triangle[2]]
                    face = mesh.faces.new((
                        mesh.verts[vert_1],
                        mesh.verts[vert_2],
                        mesh.verts[vert_3]
                    ))
                    face.smooth = True
                    for vert_index in triangle:
                        remap_loops.append(vert_index)
                    normal_1 = visual.normals[triangle[0]]
                    normal_2 = visual.normals[triangle[1]]
                    normal_3 = visual.normals[triangle[2]]
                    custom_normals.extend((
                        convert_normal_function(normal_1),
                        convert_normal_function(normal_2),
                        convert_normal_function(normal_3)
                    ))
                except ValueError:    # face already exists
                    pass

            mesh.faces.ensure_lookup_table()

            # import uvs and vertex colors
            uv_layer = mesh.loops.layers.uv.new('Texture')
            hemi_vertex_color = mesh.loops.layers.color.new('Hemi')
            current_loop = 0
            if visual.uvs_lmap:    # light maps
                lmap_uv_layer = mesh.loops.layers.uv.new('Light Map')
                for face in mesh.faces:
                    for loop in face.loops:
                        loop[uv_layer].uv = visual.uvs[remap_loops[current_loop]]
                        loop[lmap_uv_layer].uv = visual.uvs_lmap[remap_loops[current_loop]]
                        # hemi vertex color
                        hemi = visual.hemi[remap_loops[current_loop]]
                        bmesh_hemi_color = loop[hemi_vertex_color]
                        bmesh_hemi_color[0] = hemi
                        bmesh_hemi_color[1] = hemi
                        bmesh_hemi_color[2] = hemi
                        current_loop += 1
            elif visual.light:    # vertex colors
                sun_vertex_color = mesh.loops.layers.color.new('Sun')
                light_vertex_color = mesh.loops.layers.color.new('Light')
                for face in mesh.faces:
                    for loop in face.loops:
                        loop[uv_layer].uv = visual.uvs[remap_loops[current_loop]]
                        # hemi vertex color
                        hemi = visual.hemi[remap_loops[current_loop]]
                        bmesh_hemi_color = loop[hemi_vertex_color]
                        bmesh_hemi_color[0] = hemi
                        bmesh_hemi_color[1] = hemi
                        bmesh_hemi_color[2] = hemi
                        # light vertex color
                        light = visual.light[remap_loops[current_loop]]
                        bmesh_light_color = loop[light_vertex_color]
                        bmesh_light_color[0] = light[0]
                        bmesh_light_color[1] = light[1]
                        bmesh_light_color[2] = light[2]
                        # sun vertex color
                        sun = visual.sun[remap_loops[current_loop]]
                        bmesh_sun_color = loop[sun_vertex_color]
                        bmesh_sun_color[0] = sun
                        bmesh_sun_color[1] = sun
                        bmesh_sun_color[2] = sun
                        current_loop += 1
            else:    # trees
                for face in mesh.faces:
                    for loop in face.loops:
                        loop[uv_layer].uv = visual.uvs[remap_loops[current_loop]]
                        # hemi vertex color
                        hemi = visual.hemi[remap_loops[current_loop]]
                        bmesh_hemi_color = loop[hemi_vertex_color]
                        bmesh_hemi_color[0] = hemi
                        bmesh_hemi_color[1] = hemi
                        bmesh_hemi_color[2] = hemi
                        current_loop += 1

        else:    # xrlc version <= 10
            if visual.normals:
                for triangle in visual.triangles:
                    try:
                        vert_1 = remap_vertices[triangle[0]]
                        vert_2 = remap_vertices[triangle[1]]
                        vert_3 = remap_vertices[triangle[2]]
                        face = mesh.faces.new((
                            mesh.verts[vert_1],
                            mesh.verts[vert_2],
                            mesh.verts[vert_3]
                        ))
                        face.smooth = True
                        for vert_index in triangle:
                            remap_loops.append(vert_index)
                        normal_1 = visual.normals[triangle[0]]
                        normal_2 = visual.normals[triangle[1]]
                        normal_3 = visual.normals[triangle[2]]
                        custom_normals.extend((
                            convert_normal(normal_1),
                            convert_normal(normal_2),
                            convert_normal(normal_3)
                        ))
                    except ValueError:    # face already exists
                        pass
            else:
                for triangle in visual.triangles:
                    try:
                        vert_1 = remap_vertices[triangle[0]]
                        vert_2 = remap_vertices[triangle[1]]
                        vert_3 = remap_vertices[triangle[2]]
                        face = mesh.faces.new((
                            mesh.verts[vert_1],
                            mesh.verts[vert_2],
                            mesh.verts[vert_3]
                        ))
                        face.smooth = True
                        for vert_index in triangle:
                            remap_loops.append(vert_index)
                    except ValueError:    # face already exists
                        pass

            mesh.faces.ensure_lookup_table()

            # import uvs and vertex colors
            uv_layer = mesh.loops.layers.uv.new('Texture')
            current_loop = 0
            if visual.uvs_lmap:    # light maps
                lmap_uv_layer = mesh.loops.layers.uv.new('Light Map')
                for face in mesh.faces:
                    for loop in face.loops:
                        loop[uv_layer].uv = visual.uvs[remap_loops[current_loop]]
                        loop[lmap_uv_layer].uv = visual.uvs_lmap[remap_loops[current_loop]]
                        current_loop += 1
            elif visual.light:    # vertex colors
                light_vertex_color = mesh.loops.layers.color.new('Light')
                for face in mesh.faces:
                    for loop in face.loops:
                        loop[uv_layer].uv = visual.uvs[remap_loops[current_loop]]
                        # light vertex color
                        light = visual.light[remap_loops[current_loop]]
                        bmesh_light_color = loop[light_vertex_color]
                        bmesh_light_color[0] = light[0]
                        bmesh_light_color[1] = light[1]
                        bmesh_light_color[2] = light[2]
                        current_loop += 1
            else:
                for face in mesh.faces:
                    for loop in face.loops:
                        loop[uv_layer].uv = visual.uvs[remap_loops[current_loop]]
                        current_loop += 1

        # normals
        mesh.normal_update()

        # create mesh
        bpy_mesh = bpy.data.meshes.new(visual.name)
        bpy_mesh.use_auto_smooth = True
        bpy_mesh.auto_smooth_angle = math.pi
        mesh.to_mesh(bpy_mesh)
        if custom_normals:
            bpy_mesh.normals_split_custom_set(custom_normals)
        del mesh
        level.loaded_geometry[geometry_key] = bpy_mesh

    else:
        bpy_mesh = level.loaded_geometry[geometry_key]

    bpy_object = create_object(visual.name, bpy_mesh)
    return bpy_object


def import_fastpath_gcontainer(data, visual, level):
    packed_reader = xray_io.PackedReader(data)

    vb_index = packed_reader.getf('<I')[0]
    vb_offset = packed_reader.getf('<I')[0]
    vb_size = packed_reader.getf('<I')[0]
    ib_index = packed_reader.getf('<I')[0]
    ib_offset = packed_reader.getf('<I')[0]
    ib_size = packed_reader.getf('<I')[0]

    vb_slice = slice(vb_offset, vb_offset + vb_size)
    geometry_key = (vb_index, vb_offset, vb_size, ib_index, ib_offset, ib_size)
    bpy_mesh = level.loaded_fastpath_geometry.get(geometry_key, None)
    if bpy_mesh:
        return bpy_mesh, geometry_key
    vertex_buffers = level.fastpath_vertex_buffers
    indices_buffers = level.fastpath_indices_buffers
    visual.vertices = vertex_buffers[vb_index].position[vb_slice]

    visual.indices = indices_buffers[ib_index][
        ib_offset : ib_offset + ib_size
    ]
    visual.indices_count = ib_size

    return bpy_mesh, geometry_key


def read_gcontainer_v4(data):
    packed_reader = xray_io.PackedReader(data)

    vb_index = packed_reader.getf('<I')[0]
    vb_offset = packed_reader.getf('<I')[0]
    vb_size = packed_reader.getf('<I')[0]
    ib_index = packed_reader.getf('<I')[0]
    ib_offset = packed_reader.getf('<I')[0]
    ib_size = packed_reader.getf('<I')[0]

    return vb_index, vb_offset, vb_size, ib_index, ib_offset, ib_size


def import_gcontainer(
        visual, level,
        vb_index, vb_offset, vb_size,
        ib_index, ib_offset, ib_size
    ):

    if not (vb_index is None and vb_offset is None and vb_size is None):
        vb_slice = slice(vb_offset, vb_offset + vb_size)
        geometry_key = (vb_index, vb_offset, vb_size, ib_index, ib_offset, ib_size)
        bpy_mesh = level.loaded_geometry.get(geometry_key, None)
        if bpy_mesh:
            return bpy_mesh, geometry_key
        vertex_buffers = level.vertex_buffers
        indices_buffers = level.indices_buffers
        visual.vertices = vertex_buffers[vb_index].position[vb_slice]
        visual.normals = vertex_buffers[vb_index].normal[vb_slice]
        visual.uvs = vertex_buffers[vb_index].uv[vb_slice]
        visual.uvs_lmap = vertex_buffers[vb_index].uv_lmap[vb_slice]
        visual.hemi = vertex_buffers[vb_index].color_hemi[vb_slice]
        visual.vb_index = vb_index

        if vertex_buffers[vb_index].color_light:
            visual.light = vertex_buffers[vb_index].color_light[vb_slice]
        if vertex_buffers[vb_index].color_sun:
            visual.sun = vertex_buffers[vb_index].color_sun[vb_slice]
    else:
        bpy_mesh = None
        geometry_key = None

    if not (ib_index is None and ib_offset is None and ib_size is None):
        visual.indices = indices_buffers[ib_index][
            ib_offset : ib_offset + ib_size
        ]
        visual.indices_count = ib_size

    return bpy_mesh, geometry_key


def import_vcontainer(data):
    pass


def import_indices(data):
    pass


def read_indices_v3(data, visual):
    packed_reader = xray_io.PackedReader(data)
    indices_count = packed_reader.getf('I')[0]
    visual.indices_count = indices_count
    visual.indices = [packed_reader.getf('H')[0] for i in range(indices_count)]


def read_vertices_v3(data, visual, level):
    packed_reader = xray_io.PackedReader(data)
    vb = level_vb.import_vertex_buffer_d3d7(packed_reader, level)
    visual.vertices = vb.position
    visual.normals = vb.normal
    visual.uvs = vb.uv
    visual.uvs_lmap = vb.uv_lmap


def import_vertices(data):
    pass


def import_texture(data):
    pass


def import_fastpath(data, visual, level):
    chunked_reader = xray_io.ChunkedReader(data)
    chunks = {}
    for chunk_id, chunkd_data in chunked_reader:
        chunks[chunk_id] = chunkd_data
    del chunked_reader

    gcontainer_chunk_data = chunks.pop(fmt.Chunks_v4.GCONTAINER)
    import_fastpath_gcontainer(gcontainer_chunk_data, visual, level)
    del gcontainer_chunk_data

    swi_chunk_data = chunks.pop(fmt.Chunks_v4.SWIDATA, None)
    if swi_chunk_data:
        packed_reader = xray_io.PackedReader(swi_chunk_data)
        swi = imp_swi.import_slide_window_item(packed_reader)
        visual.indices = visual.indices[swi[0].offset : ]
        visual.indices_count = swi[0].triangles_count * 3
        del swi_chunk_data

    for chunk_id in chunks.keys():
        print('UNKNOW OGF FASTPATH CHUNK: {0:#x}'.format(chunk_id))


def check_unread_chunks(chunks, context=''):
    chunks_ids = list(chunks.keys())
    chunks_ids.sort()
    if chunks:
        print('There are OGF unread {1} chunks: {0}'.format(
            list(map(hex, chunks_ids)), context
        ))


def import_children_l(data, visual, level, visual_type):
    packed_reader = xray_io.PackedReader(data)
    hierrarhy_visual = HierrarhyVisual()
    hierrarhy_visual.children_count = packed_reader.getf('I')[0]
    hierrarhy_visual.index = visual.visual_id
    hierrarhy_visual.visual_type = visual_type

    if len(data) == 4 + 4 * hierrarhy_visual.children_count:
        child_format = 'I'
    elif len(data) == 4 + 2 * hierrarhy_visual.children_count:
        # used in agroprom 2215 (version 13)
        child_format = 'H'
    else:
        raise BaseException('Bad OGF CHILDREN_L data')

    for child_index in range(hierrarhy_visual.children_count):
        child = packed_reader.getf(child_format)[0]
        hierrarhy_visual.children.append(child)

    level.hierrarhy_visuals.append(hierrarhy_visual)


def import_hierrarhy_visual(chunks, visual, level):
    if visual.format_version == fmt.FORMAT_VERSION_4:
        chunks_ids = fmt.Chunks_v4
    elif visual.format_version in (fmt.FORMAT_VERSION_3, fmt.FORMAT_VERSION_2):

        if visual.format_version == fmt.FORMAT_VERSION_3:
            chunks_ids = fmt.Chunks_v3
        else:
            chunks_ids = fmt.Chunks_v2

        # bbox
        bbox_data = chunks.pop(chunks_ids.BBOX)
        read_bbox_v3(bbox_data)

        # bsphere
        bsphere_data = chunks.pop(chunks_ids.BSPHERE, None)
        if bsphere_data:
            read_bsphere_v3(bsphere_data)

    visual.name = 'hierrarhy'
    children_l_data = chunks.pop(chunks_ids.CHILDREN_L)
    import_children_l(children_l_data, visual, level, 'HIERRARHY')
    del children_l_data
    bpy_object = create_object(visual.name, None)
    check_unread_chunks(chunks, context='HIERRARHY_VISUAL')
    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'HIERRARHY'
    return bpy_object


def read_bbox_v3(data):
    packed_reader = xray_io.PackedReader(data)

    bbox_min = packed_reader.getf('3f')
    bbox_max = packed_reader.getf('3f')


def read_bsphere_v3(data):
    packed_reader = xray_io.PackedReader(data)

    center = packed_reader.getf('3f')
    radius = packed_reader.getf('f')[0]


def read_container_v3(data):
    packed_reader = xray_io.PackedReader(data)

    buffer_index = packed_reader.getf('I')[0]
    buffer_offset = packed_reader.getf('I')[0]
    buffer_size = packed_reader.getf('I')[0]

    return buffer_index, buffer_offset, buffer_size


def import_geometry(chunks, visual, level):
    if visual.format_version == fmt.FORMAT_VERSION_4:
        chunks_ids = fmt.Chunks_v4
        gcontainer_data = chunks.pop(chunks_ids.GCONTAINER, None)
        if gcontainer_data:
            vb_index, vb_offset, vb_size, ib_index, ib_offset, ib_size = read_gcontainer_v4(gcontainer_data)
            del gcontainer_data
        else:
            # vcontainer
            vcontainer_data = chunks.pop(chunks_ids.VCONTAINER)
            vb_index, vb_offset, vb_size = read_container_v3(vcontainer_data)

            # icontainer
            icontainer_data = chunks.pop(chunks_ids.ICONTAINER)
            ib_index, ib_offset, ib_size = read_container_v3(icontainer_data)

        fastpath_data = chunks.pop(chunks_ids.FASTPATH, None)    # optional chunk
        if fastpath_data:
            visual.fastpath = True
        else:
            visual.fastpath = False
        del fastpath_data

    elif visual.format_version in (fmt.FORMAT_VERSION_3, fmt.FORMAT_VERSION_2):

        if visual.format_version == fmt.FORMAT_VERSION_3:
            chunks_ids = fmt.Chunks_v3
        else:
            chunks_ids = fmt.Chunks_v2

        # bbox
        bbox_data = chunks.pop(chunks_ids.BBOX)
        read_bbox_v3(bbox_data)

        # bsphere
        bsphere_data = chunks.pop(chunks_ids.BSPHERE)
        read_bsphere_v3(bsphere_data)

        # vcontainer
        vcontainer_data = chunks.pop(chunks_ids.VCONTAINER, None)
        if vcontainer_data:
            vb_index, vb_offset, vb_size = read_container_v3(vcontainer_data)
        else:
            vertices_data = chunks.pop(chunks_ids.VERTICES)
            read_vertices_v3(vertices_data, visual, level)
            vb_index = None
            vb_offset = None
            vb_size = None

        # icontainer
        icontainer_data = chunks.pop(chunks_ids.ICONTAINER, None)
        if icontainer_data:
            ib_index, ib_offset, ib_size = read_container_v3(icontainer_data)
        else:
            indices_data = chunks.pop(chunks_ids.INDICES)
            read_indices_v3(indices_data, visual)
            ib_index = None
            ib_offset = None
            ib_size = None

    bpy_mesh, geometry_key = import_gcontainer(
        visual, level,
        vb_index, vb_offset, vb_size,
        ib_index, ib_offset, ib_size
    )

    return bpy_mesh, geometry_key


def convert_indices_to_triangles(visual):
    visual.triangles = []
    for index in range(0, visual.indices_count, 3):
        visual.triangles.append((
            visual.indices[index],
            visual.indices[index + 2],
            visual.indices[index + 1]
        ))
    del visual.indices
    del visual.indices_count


def import_normal_visual(chunks, visual, level):
    visual.name = 'normal'
    bpy_mesh, geometry_key = import_geometry(chunks, visual, level)
    check_unread_chunks(chunks, context='NORMAL_VISUAL')

    if not bpy_mesh:
        convert_indices_to_triangles(visual)
        bpy_object = create_visual(bpy_mesh, visual, level, geometry_key)
        assign_material(bpy_object, visual, level)
        if visual.fastpath:
            bpy_object.xray.level.use_fastpath = True
        else:
            bpy_object.xray.level.use_fastpath = False
    else:
        bpy_object = create_object(visual.name, bpy_mesh)

    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'NORMAL'
    return bpy_object


def ogf_color(level, packed_reader, bpy_obj, mode='SCALE'):
    xray_level = bpy_obj.xray.level

    if level.xrlc_version >= level_fmt.VERSION_11:
        rgb = packed_reader.getf('3f')
        hemi = packed_reader.getf('f')[0]
        sun = packed_reader.getf('f')[0]
    else:
        rgb = packed_reader.getf('3f')
        hemi = packed_reader.getf('f')[0]    # unkonwn
        sun = 1.0

    if mode == 'SCALE':
        xray_level.color_scale_rgb = rgb
        xray_level.color_scale_hemi = (hemi, hemi, hemi)
        xray_level.color_scale_sun = (sun, sun, sun)
    elif mode == 'BIAS':
        xray_level.color_bias_rgb = rgb
        xray_level.color_bias_hemi = (hemi, hemi, hemi)
        xray_level.color_bias_sun = (sun, sun, sun)
    else:
        raise BaseException('Unknown ogf color mode: {}'.format(mode))


def import_tree_def_2(level, visual, chunks, bpy_object):
    if visual.format_version == fmt.FORMAT_VERSION_4:
        chunks_ids = fmt.Chunks_v4
    elif visual.format_version == fmt.FORMAT_VERSION_3:
        chunks_ids = fmt.Chunks_v3

    tree_def_2_data = chunks.pop(chunks_ids.TREEDEF2)
    packed_reader = xray_io.PackedReader(tree_def_2_data)
    del tree_def_2_data

    tree_xform = packed_reader.getf('16f')
    ogf_color(level, packed_reader, bpy_object, mode='SCALE')    # c_scale
    ogf_color(level, packed_reader, bpy_object, mode='BIAS')    # c_bias

    return tree_xform


def set_tree_transforms(bpy_object, xform):
    transform_matrix = mathutils.Matrix((
        (xform[0], xform[1], xform[2], xform[3]),
        (xform[4], xform[5], xform[6], xform[7]),
        (xform[8], xform[9], xform[10], xform[11]),
        (xform[12], xform[13], xform[14], xform[15])
        ))
    transform_matrix.transpose()
    translate, rotate, scale = transform_matrix.decompose()
    bpy_object.location = translate[0], translate[2], translate[1]
    bpy_object.scale = scale[0], scale[2], scale[1]
    rotate = rotate.to_euler('ZXY')
    bpy_object.rotation_euler = -rotate[0], -rotate[2], -rotate[1]


def import_tree_st_visual(chunks, visual, level):
    visual.name = 'tree_st'
    bpy_mesh, geometry_key = import_geometry(chunks, visual, level)
    if not bpy_mesh:
        convert_indices_to_triangles(visual)
        bpy_object = create_visual(bpy_mesh, visual, level, geometry_key)
        assign_material(bpy_object, visual, level)
    else:
        bpy_object = create_object(visual.name, bpy_mesh)
    tree_xform = import_tree_def_2(level, visual, chunks, bpy_object)
    set_tree_transforms(bpy_object, tree_xform)
    check_unread_chunks(chunks, context='TREE_ST_VISUAL')
    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'TREE_ST'
    return bpy_object


def import_swidata(chunks):
    swi_data = chunks.pop(fmt.Chunks_v4.SWIDATA)
    packed_reader = xray_io.PackedReader(swi_data)
    del swi_data
    swi = imp_swi.import_slide_window_item(packed_reader)
    del packed_reader
    return swi


def import_progressive_visual(chunks, visual, level):
    visual.name = 'progressive'
    bpy_mesh, geometry_key = import_geometry(chunks, visual, level)
    swi = import_swidata(chunks)

    visual.indices = visual.indices[swi[0].offset : ]
    visual.indices_count = swi[0].triangles_count * 3
    convert_indices_to_triangles(visual)

    check_unread_chunks(chunks, context='PROGRESSIVE_VISUAL')

    if not bpy_mesh:
        bpy_object = create_visual(bpy_mesh, visual, level, geometry_key)
        assign_material(bpy_object, visual, level)
        if visual.fastpath:
            bpy_object.xray.level.use_fastpath = True
        else:
            bpy_object.xray.level.use_fastpath = False
    else:
        bpy_object = create_object(visual.name, bpy_mesh)

    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'PROGRESSIVE'
    return bpy_object


def import_swicontainer(chunks):
    swicontainer_data = chunks.pop(fmt.Chunks_v4.SWICONTAINER)
    packed_reader = xray_io.PackedReader(swicontainer_data)
    del swicontainer_data
    swi_index = packed_reader.getf('I')[0]
    return swi_index


def get_float_rgb_hemi(rgb_hemi):
    hemi = (rgb_hemi & (0xff << 24)) >> 24
    r = (rgb_hemi & (0xff << 16)) >> 16
    g = (rgb_hemi & (0xff << 8)) >> 8
    b = rgb_hemi & 0xff
    return r / 0xff, g / 0xff, b / 0xff, hemi / 0xff


def import_lod_def_2(level, data):
    packed_reader = xray_io.PackedReader(data)
    verts = []
    uvs = []
    lights = {'rgb': [], 'hemi': [], 'sun': []}
    faces = []
    if level.xrlc_version >= level_fmt.VERSION_11:
        for i in range(8):
            face = []
            for j in range(4):
                coord_x, coord_y, coord_z = packed_reader.getf('<3f')
                verts.append((coord_x, coord_z, coord_y))
                face.append(i * 4 + j)
                coord_u, coord_v = packed_reader.getf('<2f')
                uvs.append((coord_u, 1 - coord_v))
                # import vertex light
                rgb_hemi = packed_reader.getf('<I')[0]
                r, g, b, hemi = get_float_rgb_hemi(rgb_hemi)
                sun = packed_reader.getf('<B')[0]
                sun = sun / 0xff
                packed_reader.getf('<3B')    # pad (unused)
                lights['rgb'].append((r, g, b, 1.0))
                lights['hemi'].append(hemi)
                lights['sun'].append(sun)
            faces.append(face)
    else:
        for i in range(8):
            face = []
            for j in range(4):
                coord_x, coord_y, coord_z = packed_reader.getf('<3f')
                verts.append((coord_x, coord_z, coord_y))
                face.append(i * 4 + j)
                coord_u, coord_v = packed_reader.getf('<2f')
                uvs.append((coord_u, 1 - coord_v))
                # import vertex light
                rgb_hemi = packed_reader.getf('<I')[0]
                r, g, b, hemi = get_float_rgb_hemi(rgb_hemi)
                lights['rgb'].append((r, g, b, 1.0))
                lights['hemi'].append(1.0)
                lights['sun'].append(1.0)
            faces.append(face)
    return verts, uvs, lights, faces


def import_lod_visual(chunks, visual, level):
    if visual.format_version == fmt.FORMAT_VERSION_4:
        chunks_ids = fmt.Chunks_v4
    elif visual.format_version == fmt.FORMAT_VERSION_3:
        chunks_ids = fmt.Chunks_v3

        # bbox
        bbox_data = chunks.pop(chunks_ids.BBOX)
        read_bbox_v3(bbox_data)

        # bsphere
        bsphere_data = chunks.pop(chunks_ids.BSPHERE)
        read_bsphere_v3(bsphere_data)

    visual.name = 'lod'
    children_l_data = chunks.pop(chunks_ids.CHILDREN_L)
    import_children_l(children_l_data, visual, level, 'LOD')
    del children_l_data

    lod_def_2_data = chunks.pop(chunks_ids.LODDEF2)
    verts, uvs, lights, faces = import_lod_def_2(level, lod_def_2_data)
    del lod_def_2_data

    check_unread_chunks(chunks, context='LOD_VISUAL')

    bpy_mesh = bpy.data.meshes.new(visual.name)
    bpy_mesh.from_pydata(verts, (), faces)
    uv_layer = bpy_mesh.uv_layers.new(name='Texture')
    rgb_color = bpy_mesh.vertex_colors.new(name='Light')
    hemi_color = bpy_mesh.vertex_colors.new(name='Hemi')
    sun_color = bpy_mesh.vertex_colors.new(name='Sun')
    for face in bpy_mesh.polygons:
        for loop_index in face.loop_indices:
            loop = bpy_mesh.loops[loop_index]
            vert_index = loop.vertex_index
            uv = uvs[vert_index]
            rgb = lights['rgb'][vert_index]
            hemi = lights['hemi'][vert_index]
            sun = lights['sun'][vert_index]
            uv_layer.data[loop.index].uv = uv
            rgb_color.data[loop.index].color = rgb
            hemi_color.data[loop.index].color = (hemi, hemi, hemi, 1.0)
            sun_color.data[loop.index].color = (sun, sun, sun, 1.0)
    bpy_object = create_object(visual.name, bpy_mesh)
    assign_material(bpy_object, visual, level)
    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'LOD'
    return bpy_object


def import_tree_pm_visual(chunks, visual, level):
    visual.name = 'tree_pm'
    bpy_mesh, geometry_key = import_geometry(chunks, visual, level)
    swi_index = import_swicontainer(chunks)
    if not bpy_mesh:
        swi = level.swis[swi_index]
        visual.indices = visual.indices[swi[0].offset : ]
        visual.indices_count = swi[0].triangles_count * 3
        convert_indices_to_triangles(visual)

        bpy_object = create_visual(bpy_mesh, visual, level, geometry_key)
        assign_material(bpy_object, visual, level)
    else:
        bpy_object = create_object(visual.name, bpy_mesh)
    tree_xform = import_tree_def_2(level, visual, chunks, bpy_object)
    set_tree_transforms(bpy_object, tree_xform)
    check_unread_chunks(chunks, context='TREE_PM_VISUAL')
    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'TREE_PM'
    return bpy_object


def import_model_v4(chunks, visual, level):

    if visual.model_type == fmt.ModelType_v4.NORMAL:
        bpy_obj = import_normal_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType_v4.HIERRARHY:
        bpy_obj = import_hierrarhy_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType_v4.PROGRESSIVE:
        bpy_obj = import_progressive_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType_v4.TREE_ST:
        bpy_obj = import_tree_st_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType_v4.TREE_PM:
        bpy_obj = import_tree_pm_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType_v4.LOD:
        bpy_obj = import_lod_visual(chunks, visual, level)

    else:
        raise BaseException('unsupported model type: {:x}'.format(
            visual.model_type
        ))

    data = bpy_obj.xray
    data.is_ogf = True

    scene_collection = bpy.context.scene.collection
    collection_name = level_create.LEVEL_COLLECTIONS_NAMES_TABLE[visual.name]
    collection = level.collections[collection_name]
    collection.objects.link(bpy_obj)
    scene_collection.objects.unlink(bpy_obj)
    level.visuals.append(bpy_obj)


def import_texture_and_shader_v3(visual, level, data):
    packed_reader = xray_io.PackedReader(data)
    visual.texture_id = packed_reader.getf('I')[0]
    visual.shader_id = packed_reader.getf('I')[0]


def import_model_v3(chunks, visual, level):
    chunks_ids = fmt.Chunks_v3
    if visual.model_type == fmt.ModelType_v3.NORMAL:
        texture_l_data = chunks.get(chunks_ids.TEXTURE_L)
        if texture_l_data:
            chunks.pop(chunks_ids.TEXTURE_L)
            import_texture_and_shader_v3(visual, level, texture_l_data)
        bpy_obj = import_normal_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType_v3.HIERRARHY:
        bpy_obj = import_hierrarhy_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType_v3.TREE:
        texture_l_data = chunks.get(chunks_ids.TEXTURE_L)
        if texture_l_data:
            chunks.pop(chunks_ids.TEXTURE_L)
            import_texture_and_shader_v3(visual, level, texture_l_data)
        bpy_obj = import_tree_st_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType_v3.LOD:
        texture_l_data = chunks.get(chunks_ids.TEXTURE_L)
        if texture_l_data:
            chunks.pop(chunks_ids.TEXTURE_L)
            import_texture_and_shader_v3(visual, level, texture_l_data)
        bpy_obj = import_lod_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType_v3.CACHED:
        texture_l_data = chunks.get(chunks_ids.TEXTURE_L)
        if texture_l_data:
            chunks.pop(chunks_ids.TEXTURE_L)
            import_texture_and_shader_v3(visual, level, texture_l_data)
        bpy_obj = import_normal_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType_v3.PROGRESSIVE2:
        ####################################################
        # DELETE
        ####################################################
        bpy_obj = bpy.data.objects.new('PROGRESSIVE2', None)
        bpy.context.scene.collection.objects.link(bpy_obj)
        visual.name = 'progressive'

    else:
        raise BaseException('unsupported model type: 0x{:x}'.format(
            visual.model_type
        ))

    data = bpy_obj.xray
    data.is_ogf = True

    scene_collection = bpy.context.scene.collection
    collection_name = level_create.LEVEL_COLLECTIONS_NAMES_TABLE[visual.name]
    collection = level.collections[collection_name]
    collection.objects.link(bpy_obj)
    scene_collection.objects.unlink(bpy_obj)
    level.visuals.append(bpy_obj)


def import_model_v2(chunks, visual, level):
    chunks_ids = fmt.Chunks_v2
    if visual.model_type == fmt.ModelType_v2.NORMAL:
        texture_l_data = chunks.pop(chunks_ids.TEXTURE_L)
        import_texture_and_shader_v3(visual, level, texture_l_data)
        bpy_obj = import_normal_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType_v2.HIERRARHY:
        bpy_obj = import_hierrarhy_visual(chunks, visual, level)
    else:
        raise BaseException('unsupported model type: 0x{:x}'.format(
            visual.model_type
        ))

    data = bpy_obj.xray
    data.is_ogf = True

    scene_collection = bpy.context.scene.collection
    collection_name = level_create.LEVEL_COLLECTIONS_NAMES_TABLE[visual.name]
    collection = level.collections[collection_name]
    collection.objects.link(bpy_obj)
    scene_collection.objects.unlink(bpy_obj)
    level.visuals.append(bpy_obj)


def import_bounding_sphere(packed_reader):
    center = packed_reader.getf('<3f')
    radius = packed_reader.getf('<f')[0]


def import_bounding_box(packed_reader):
    bbox_min = packed_reader.getf('<3f')
    bbox_max = packed_reader.getf('<3f')


def check_version(visual):
    if visual.format_version not in fmt.SUPPORT_FORMAT_VERSIONS:
        raise BaseException(
            'Unsupported ogf format version: {}'.format(visual.format_version)
        )


def import_header(data, visual):
    packed_reader = xray_io.PackedReader(data)
    visual.format_version = packed_reader.getf('<B')[0]
    check_version(visual)
    if visual.format_version == fmt.FORMAT_VERSION_4:
        visual.model_type = packed_reader.getf('<B')[0]
        visual.shader_id = packed_reader.getf('<H')[0]
        import_bounding_box(packed_reader)
        import_bounding_sphere(packed_reader)
    elif visual.format_version in (fmt.FORMAT_VERSION_3, fmt.FORMAT_VERSION_2):
        visual.model_type = packed_reader.getf('<B')[0]
        visual.shader_id = packed_reader.getf('<H')[0]


def import_main(chunks, visual, level):
    header_chunk_data = chunks.pop(fmt.HEADER)
    import_header(header_chunk_data, visual)

    # version 4
    if visual.format_version == fmt.FORMAT_VERSION_4:
        import_function = import_model_v4
        chunks_names = fmt.chunks_names_v4
        model_type_names = fmt.model_type_names_v4

    # version 3
    elif visual.format_version == fmt.FORMAT_VERSION_3:
        import_function = import_model_v3
        chunks_names = fmt.chunks_names_v3
        model_type_names = fmt.model_type_names_v3

    # version 2
    elif visual.format_version == fmt.FORMAT_VERSION_2:
        import_function = import_model_v2
        chunks_names = fmt.chunks_names_v2
        model_type_names = fmt.model_type_names_v2

    key = []
    for chunk_id in chunks.keys():
        key.append(chunks_names[chunk_id])
    key.append('HEADER')
    key.sort()
    key.insert(0, model_type_names[visual.model_type])
    key = tuple(key)
    level.visual_keys.add(key)
    import_function(chunks, visual, level)


def get_ogf_chunks(data):
    chunked_reader = xray_io.ChunkedReader(data)
    del data
    chunks = {}
    chunks_ids = set()
    for chunk_id, chunkd_data in chunked_reader:
        chunks[chunk_id] = chunkd_data
        chunks_ids.add(hex(chunk_id))
    del chunked_reader
    return chunks, chunks_ids


def import_(data, visual_id, level, chunks, visuals_ids):
    chunks, visual_chunks_ids = get_ogf_chunks(data)
    visual = Visual()
    visual.visual_id = visual_id
    import_main(chunks, visual, level)
