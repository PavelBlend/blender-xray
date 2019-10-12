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


class HierrarhyVisual(object):
    def __init__(self):
        self.index = None
        self.children = []
        self.children_count = None


def assign_material(bpy_object, shader_id, materials):
    bpy_object.data.materials.append(materials[shader_id])


def create_object(name, obj_data):
    bpy_object = bpy.data.objects.new(name, obj_data)
    bpy.context.scene.collection.objects.link(bpy_object)
    return bpy_object


def create_visual(bpy_mesh, visual, level, geometry_key):

    if not bpy_mesh:
        mesh = bmesh.new()

        # import vertices
        for vertex_coord in visual.vertices:
            mesh.verts.new(vertex_coord)

        mesh.verts.ensure_lookup_table()
        mesh.verts.index_update()

        # import triangles
        for triangle in visual.triangles:
            mesh.faces.new((
                mesh.verts[triangle[0]],
                mesh.verts[triangle[1]],
                mesh.verts[triangle[2]]
            ))

        mesh.faces.ensure_lookup_table()

        # import uvs and vertex colors
        uv_layer = mesh.loops.layers.uv.new('Texture')
        hemi_vertex_color = mesh.loops.layers.color.new('Hemi')
        if visual.uvs_lmap:    # light maps
            lmap_uv_layer = mesh.loops.layers.uv.new('Light Map')
            for face in mesh.faces:
                for loop in face.loops:
                    loop[uv_layer].uv = visual.uvs[loop.vert.index]
                    loop[lmap_uv_layer].uv = visual.uvs_lmap[loop.vert.index]
                    # hemi vertex color
                    hemi = visual.hemi[loop.vert.index]
                    bmesh_hemi_color = loop[hemi_vertex_color]
                    bmesh_hemi_color[0] = hemi
                    bmesh_hemi_color[1] = hemi
                    bmesh_hemi_color[2] = hemi
        elif visual.light:    # vertex colors
            sun_vertex_color = mesh.loops.layers.color.new('Sun')
            light_vertex_color = mesh.loops.layers.color.new('Light')
            for face in mesh.faces:
                for loop in face.loops:
                    loop[uv_layer].uv = visual.uvs[loop.vert.index]
                    # hemi vertex color
                    hemi = visual.hemi[loop.vert.index]
                    bmesh_hemi_color = loop[hemi_vertex_color]
                    bmesh_hemi_color[0] = hemi
                    bmesh_hemi_color[1] = hemi
                    bmesh_hemi_color[2] = hemi
                    # light vertex color
                    light = visual.light[loop.vert.index]
                    bmesh_light_color = loop[light_vertex_color]
                    bmesh_light_color[0] = light[0]
                    bmesh_light_color[1] = light[1]
                    bmesh_light_color[2] = light[2]
                    # sun vertex color
                    sun = visual.sun[loop.vert.index]
                    bmesh_sun_color = loop[sun_vertex_color]
                    bmesh_sun_color[0] = sun
                    bmesh_sun_color[1] = sun
                    bmesh_sun_color[2] = sun
        else:    # trees
            for face in mesh.faces:
                for loop in face.loops:
                    loop[uv_layer].uv = visual.uvs[loop.vert.index]
                    # hemi vertex color
                    hemi = visual.hemi[loop.vert.index]
                    bmesh_hemi_color = loop[hemi_vertex_color]
                    bmesh_hemi_color[0] = hemi
                    bmesh_hemi_color[1] = hemi
                    bmesh_hemi_color[2] = hemi

        # normals
        mesh.normal_update()

        # create mesh
        bpy_mesh = bpy.data.meshes.new(visual.name)
        mesh.to_mesh(bpy_mesh)
        del mesh
        level.loaded_geometry[geometry_key] = bpy_mesh

    else:
        bpy_mesh = level.loaded_geometry[geometry_key]

    bpy_object = create_object(visual.name, bpy_mesh)
    return bpy_object


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
    visual.vertices = level.vertex_buffers[vb_index].position[vb_slice]
    visual.uvs = level.vertex_buffers[vb_index].uv[vb_slice]
    visual.uvs_lmap = level.vertex_buffers[vb_index].uv_lmap[vb_slice]
    visual.hemi = level.vertex_buffers[vb_index].color_hemi[vb_slice]

    if level.vertex_buffers[vb_index].color_light:
        visual.light = level.vertex_buffers[vb_index].color_light[vb_slice]
    if level.vertex_buffers[vb_index].color_sun:
        visual.sun = level.vertex_buffers[vb_index].color_sun[vb_slice]

    visual.indices = level.indices_buffers[ib_index][
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


def import_fastpath(data):
    pass


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
    return bpy_object


def import_geometry(chunks, visual, level):
    gcontainer_data = chunks.pop(fmt.Chunks.GCONTAINER)
    bpy_mesh, geometry_key = import_gcontainer(gcontainer_data, visual, level)
    del gcontainer_data

    fastpath_data = chunks.pop(fmt.Chunks.FASTPATH, None)    # optional chunk
    if fastpath_data:
        import_fastpath(fastpath_data)
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
        assign_material(bpy_object, visual.shader_id, level.materials)
    else:
        bpy_object = create_object(visual.name, bpy_mesh)

    return bpy_object


def ogf_color(packed_reader, bpy_obj, mode='SCALE'):
    if mode == 'SCALE':
        property_group = bpy_obj.xray.ogf.color_scale
    elif mode == 'BIAS':
        property_group = bpy_obj.xray.ogf.color_bias
    else:
        raise BaseException('Unknown ogf color mode: {}'.format(mode))
    property_group.rgb = packed_reader.getf('3f')
    hemi = packed_reader.getf('f')[0]
    property_group.hemi = (hemi, hemi, hemi)
    sun = packed_reader.getf('f')[0]
    property_group.sun = (sun, sun, sun)


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
        assign_material(bpy_object, visual.shader_id, level.materials)
    else:
        bpy_object = create_object(visual.name, bpy_mesh)
    tree_xform = import_tree_def_2(chunks, bpy_object)
    set_tree_transforms(bpy_object, tree_xform)
    check_unread_chunks(chunks)
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
        assign_material(bpy_object, visual.shader_id, level.materials)
    else:
        bpy_object = create_object(visual.name, bpy_mesh)

    return bpy_object


def import_swicontainer(chunks):
    swicontainer_data = chunks.pop(fmt.Chunks.SWICONTAINER)
    packed_reader = xray_io.PackedReader(swicontainer_data)
    del swicontainer_data
    swi_index = packed_reader.getf('I')[0]
    return swi_index


def import_lod_def_2(data):
    packed_reader = xray_io.PackedReader(data)
    verts = []
    uvs = []
    faces = []
    for i in range(8):
        face = []
        for j in range(4):
            coord_x, coord_y, coord_z = packed_reader.getf('3f')
            verts.append((coord_x, coord_z, coord_y))
            face.append(i * 4 + j)
            coord_u, coord_v = packed_reader.getf('2f')
            uvs.append((coord_u, 1 - coord_v))
            # TODO: import vertex light
            hemi = packed_reader.getf('I')[0]
            sun = packed_reader.getf('B')[0]
            pad = packed_reader.getf('3B')
        faces.append(face)
    return verts, uvs, faces


def import_lod_visual(chunks, visual, level):
    visual.name = 'lod'
    children_l_data = chunks.pop(fmt.Chunks.CHILDREN_L)
    import_children_l(children_l_data, visual, level, 'LOD')
    del children_l_data

    lod_def_2_data = chunks.pop(fmt.Chunks.LODDEF2)
    verts, uvs, faces = import_lod_def_2(lod_def_2_data)
    del lod_def_2_data

    check_unread_chunks(chunks)

    bpy_mesh = bpy.data.meshes.new(visual.name)
    bpy_mesh.from_pydata(verts, (), faces)
    uv_layer = bpy_mesh.uv_layers.new(name='Texture')
    for face in bpy_mesh.polygons:
        for loop_index in face.loop_indices:
            loop = bpy_mesh.loops[loop_index]
            vert_index = loop.vertex_index
            uv = uvs[vert_index]
            uv_layer.data[loop.index].uv = uv
    bpy_object = create_object(visual.name, bpy_mesh)
    assign_material(bpy_object, visual.shader_id, level.materials)
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
        assign_material(bpy_object, visual.shader_id, level.materials)
    else:
        bpy_object = create_object(visual.name, bpy_mesh)
    tree_xform = import_tree_def_2(chunks, bpy_object)
    set_tree_transforms(bpy_object, tree_xform)
    check_unread_chunks(chunks)
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
    # bbox min
    data.bbox_min[0] = visual.bbox_min[0]
    data.bbox_min[1] = visual.bbox_min[2]
    data.bbox_min[2] = visual.bbox_min[1]
    # bbox max
    data.bbox_max[0] = visual.bbox_max[0]
    data.bbox_max[1] = visual.bbox_max[2]
    data.bbox_max[2] = visual.bbox_max[1]
    # bsphere
    data.center[0] = visual.center[0]
    data.center[1] = visual.center[2]
    data.center[2] = visual.center[1]
    data.radius = visual.radius

    scene_collection = bpy.context.scene.collection
    collection_name = level_create.LEVEL_COLLECTIONS_NAMES_TABLE[visual.name]
    collection = level.collections[collection_name]
    collection.objects.link(bpy_obj)
    scene_collection.objects.unlink(bpy_obj)
    level.visuals.append(bpy_obj)


def import_bounding_sphere(packed_reader, visual):
    visual.center = packed_reader.getf('<3f')
    visual.radius = packed_reader.getf('<f')[0]


def import_bounding_box(packed_reader, visual):
    visual.bbox_min = packed_reader.getf('<3f')
    visual.bbox_max = packed_reader.getf('<3f')


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
    import_bounding_box(packed_reader, visual)
    import_bounding_sphere(packed_reader, visual)


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
