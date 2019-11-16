import math

import bpy, mathutils, bmesh

from .. import xray_io
from ..level import swi as imp_swi, create as level_create
from . import fmt


class Visual(object):
    def __init__(self):
        self.visual_id = None
        self.format_version = None
        self.model_type = None
        self.shader_id = None
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


class HierrarhyVisual(object):
    def __init__(self):
        self.index = None
        self.children = []
        self.children_count = None


def assign_material(bpy_object, visual, materials):
    shader_id = visual.shader_id
    material = materials[shader_id]
    if visual.use_two_sided_tris:
        material.xray.flags_twosided = True
    bpy_object.data.materials.append(material)


def create_object(name, obj_data):
    bpy_object = bpy.data.objects.new(name, obj_data)
    bpy.context.scene.collection.objects.link(bpy_object)
    return bpy_object


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
        edge_normals_1 = {}
        edge_normals_2 = {}

        # import triangles
        remap_loops = []
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
                normals = {}
                normals[vert_1] = normal_1
                normals[vert_2] = normal_2
                normals[vert_3] = normal_3
                for edge in face.edges:
                    edge_verts = (edge.verts[0].index, edge.verts[1].index)
                    if edge_normals_1.get(edge, None) is None:
                        edge_normals_1[edge] = set()
                        edge_normals_2[edge] = set()
                    edge_normals_1[edge].add(normals[edge_verts[0]])
                    edge_normals_2[edge].add(normals[edge_verts[1]])
            except ValueError:    # face already exists
                pass

        mesh.faces.ensure_lookup_table()

        for edge, normals_1 in edge_normals_1.items():
            normals_2 = edge_normals_2[edge]
            unique_normals_1_count = len(normals_1)
            unique_normals_2_count = len(normals_2)
            if unique_normals_1_count > 1 or unique_normals_2_count > 1:
                edge.smooth = False

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

        # normals
        mesh.normal_update()

        # create mesh
        bpy_mesh = bpy.data.meshes.new(visual.name)
        bpy_mesh.use_auto_smooth = True
        bpy_mesh.auto_smooth_angle = math.pi
        mesh.to_mesh(bpy_mesh)
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


def import_gcontainer(data, visual, level):
    packed_reader = xray_io.PackedReader(data)

    vb_index = packed_reader.getf('<I')[0]
    vb_offset = packed_reader.getf('<I')[0]
    vb_size = packed_reader.getf('<I')[0]
    ib_index = packed_reader.getf('<I')[0]
    ib_offset = packed_reader.getf('<I')[0]
    ib_size = packed_reader.getf('<I')[0]

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

    if vertex_buffers[vb_index].color_light:
        visual.light = vertex_buffers[vb_index].color_light[vb_slice]
    if vertex_buffers[vb_index].color_sun:
        visual.sun = vertex_buffers[vb_index].color_sun[vb_slice]

    visual.indices = indices_buffers[ib_index][
        ib_offset : ib_offset + ib_size
    ]
    visual.indices_count = ib_size

    return bpy_mesh, geometry_key


def import_vcontainer(data):
    pass


def import_indices(data):
    pass


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

    gcontainer_chunk_data = chunks.pop(fmt.Chunks.GCONTAINER)
    import_fastpath_gcontainer(gcontainer_chunk_data, visual, level)
    del gcontainer_chunk_data

    swi_chunk_data = chunks.pop(fmt.Chunks.SWIDATA, None)
    if swi_chunk_data:
        packed_reader = xray_io.PackedReader(swi_chunk_data)
        swi = imp_swi.import_slide_window_item(packed_reader)
        visual.indices = visual.indices[swi[0].offset : ]
        visual.indices_count = swi[0].triangles_count * 3
        del swi_chunk_data

    for chunk_id in chunks.keys():
        print('UNKNOW OGF FASTPATH CHUNK: {0:#x}'.format(chunk_id))


def check_unread_chunks(chunks):
    chunks_ids = list(chunks.keys())
    chunks_ids.sort()
    if chunks:
        raise BaseException('There are unread chunks: {}'.format(chunks_ids))


def import_children_l(data, visual, level, visual_type):
    packed_reader = xray_io.PackedReader(data)
    hierrarhy_visual = HierrarhyVisual()
    hierrarhy_visual.children_count = packed_reader.getf('I')[0]
    hierrarhy_visual.index = visual.visual_id
    hierrarhy_visual.visual_type = visual_type

    for child_index in range(hierrarhy_visual.children_count):
        child = packed_reader.getf('I')[0]
        hierrarhy_visual.children.append(child)

    level.hierrarhy_visuals.append(hierrarhy_visual)


def import_hierrarhy_visual(chunks, visual, level):
    visual.name = 'hierrarhy'
    children_l_data = chunks.pop(fmt.Chunks.CHILDREN_L)
    import_children_l(children_l_data, visual, level, 'HIERRARHY')
    del children_l_data
    bpy_object = create_object(visual.name, None)
    check_unread_chunks(chunks)
    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'HIERRARHY'
    return bpy_object


def import_geometry(chunks, visual, level):
    gcontainer_data = chunks.pop(fmt.Chunks.GCONTAINER)
    bpy_mesh, geometry_key = import_gcontainer(gcontainer_data, visual, level)
    del gcontainer_data

    fastpath_data = chunks.pop(fmt.Chunks.FASTPATH, None)    # optional chunk
    if fastpath_data:
        visual.fastpath = True
    else:
        visual.fastpath = False
    del fastpath_data
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
    check_unread_chunks(chunks)

    if not bpy_mesh:
        convert_indices_to_triangles(visual)
        bpy_object = create_visual(bpy_mesh, visual, level, geometry_key)
        assign_material(bpy_object, visual, level.materials)
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


def ogf_color(packed_reader, bpy_obj, mode='SCALE'):
    level = bpy_obj.xray.level

    rgb = packed_reader.getf('3f')
    hemi = packed_reader.getf('f')[0]
    sun = packed_reader.getf('f')[0]

    if mode == 'SCALE':
        level.color_scale_rgb = rgb
        level.color_scale_hemi = (hemi, hemi, hemi)
        level.color_scale_sun = (sun, sun, sun)
    elif mode == 'BIAS':
        level.color_bias_rgb = rgb
        level.color_bias_hemi = (hemi, hemi, hemi)
        level.color_bias_sun = (sun, sun, sun)
    else:
        raise BaseException('Unknown ogf color mode: {}'.format(mode))


def import_tree_def_2(chunks, bpy_object):
    tree_def_2_data = chunks.pop(fmt.Chunks.TREEDEF2)
    packed_reader = xray_io.PackedReader(tree_def_2_data)
    del tree_def_2_data

    tree_xform = packed_reader.getf('16f')
    ogf_color(packed_reader, bpy_object, mode='SCALE')    # c_scale
    ogf_color(packed_reader, bpy_object, mode='BIAS')    # c_bias

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
        assign_material(bpy_object, visual, level.materials)
    else:
        bpy_object = create_object(visual.name, bpy_mesh)
    tree_xform = import_tree_def_2(chunks, bpy_object)
    set_tree_transforms(bpy_object, tree_xform)
    check_unread_chunks(chunks)
    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'TREE_ST'
    return bpy_object


def import_swidata(chunks):
    swi_data = chunks.pop(fmt.Chunks.SWIDATA)
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

    check_unread_chunks(chunks)

    if not bpy_mesh:
        bpy_object = create_visual(bpy_mesh, visual, level, geometry_key)
        assign_material(bpy_object, visual, level.materials)
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
    swicontainer_data = chunks.pop(fmt.Chunks.SWICONTAINER)
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


def import_lod_def_2(data):
    packed_reader = xray_io.PackedReader(data)
    verts = []
    uvs = []
    lights = {'rgb': [], 'hemi': [], 'sun': []}
    faces = []
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
    return verts, uvs, lights, faces


def import_lod_visual(chunks, visual, level):
    visual.name = 'lod'
    children_l_data = chunks.pop(fmt.Chunks.CHILDREN_L)
    import_children_l(children_l_data, visual, level, 'LOD')
    del children_l_data

    lod_def_2_data = chunks.pop(fmt.Chunks.LODDEF2)
    verts, uvs, lights, faces = import_lod_def_2(lod_def_2_data)
    del lod_def_2_data

    check_unread_chunks(chunks)

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
    assign_material(bpy_object, visual, level.materials)
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
        assign_material(bpy_object, visual, level.materials)
    else:
        bpy_object = create_object(visual.name, bpy_mesh)
    tree_xform = import_tree_def_2(chunks, bpy_object)
    set_tree_transforms(bpy_object, tree_xform)
    check_unread_chunks(chunks)
    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'TREE_PM'
    return bpy_object


def import_model(chunks, visual, level):

    if visual.model_type == fmt.ModelType.NORMAL:
        bpy_obj = import_normal_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType.HIERRARHY:
        bpy_obj = import_hierrarhy_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType.PROGRESSIVE:
        bpy_obj = import_progressive_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType.TREE_ST:
        bpy_obj = import_tree_st_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType.TREE_PM:
        bpy_obj = import_tree_pm_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType.LOD:
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
    visual.model_type = packed_reader.getf('<B')[0]
    visual.shader_id = packed_reader.getf('<H')[0]
    import_bounding_box(packed_reader)
    import_bounding_sphere(packed_reader)


def import_main(chunks, visual, level):
    header_chunk_data = chunks.pop(fmt.Chunks.HEADER)
    import_header(header_chunk_data, visual)
    import_model(chunks, visual, level)


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
