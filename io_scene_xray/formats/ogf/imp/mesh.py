# standart modules
import math

# blender modules
import bpy
import bmesh

# addon modules
from . import utility
from . import material
from .. import fmt
from ... import level
from .... import utils


def assign_visual_vertex_weights(visual, bpy_object, remap_vertices):
    if visual.weights:
        for index, (name, parent) in enumerate(visual.bones):
            if index in visual.deform_bones:
                bpy_object.vertex_groups.new(name=name)
        for index, weights in enumerate(visual.weights):
            for bone_index, weight in weights:
                bone_name, _ = visual.bones[bone_index]
                group = bpy_object.vertex_groups[bone_name]
                vert_index = remap_vertices[index]
                group.add([vert_index, ], weight, 'REPLACE')


def get_vert_normals(visual):
    temp_mesh = bmesh.new()

    # init vertex normals list and create vertices
    vert_normals = {}
    for vertex_index, vertex_coord in enumerate(visual.vertices):
        vert = temp_mesh.verts.new(vertex_coord)
        vert_normals[tuple(vert.co)] = []

    temp_mesh.verts.ensure_lookup_table()
    temp_mesh.verts.index_update()

    # create triangles
    for triangle in visual.triangles:
        try:
            temp_mesh.faces.new((
                temp_mesh.verts[triangle[0]],
                temp_mesh.verts[triangle[1]],
                temp_mesh.verts[triangle[2]]
            ))
        except ValueError:    # face already exists
            pass

    temp_mesh.faces.ensure_lookup_table()
    temp_mesh.normal_update()

    # collect vertex normals
    for vert in temp_mesh.verts:
        norm = (
            round(vert.normal[0], 3),
            round(vert.normal[1], 3),
            round(vert.normal[2], 3)
        )
        vert_normals[tuple(vert.co)].append((vert.index, norm))

    temp_mesh.clear()

    return vert_normals


def get_back_side(vert_normals):
    back_side = {}
    for vertex_co, norms in vert_normals.items():
        back_side_norms = set()
        for vertex_index, normal in norms:
            back_norm = (-normal[0], -normal[1], -normal[2])
            if back_norm in back_side_norms:
                back_side[vertex_index] = True
            else:
                back_side[vertex_index] = False
                back_side_norms.add(normal)
    return back_side


def create_static_vertices(visual, mesh, back_side):
    unique_verts = {}
    remap_verts = {}
    remap_index = 0

    for index, coord in enumerate(visual.vertices):
        is_back = back_side[index]
        new_index = unique_verts.get((coord, is_back), None)

        if new_index is None:
            mesh.verts.new(coord)
            remap_verts[index] = remap_index
            unique_verts[(coord, is_back)] = remap_index
            remap_index += 1

        else:
            remap_verts[index] = new_index

    return remap_verts


def create_skinned_vertices(visual, mesh, back_side):
    unique_verts = {}
    remap_verts = {}
    remap_index = 0

    for index, coord in enumerate(visual.vertices):
        is_back = back_side[index]
        weights = tuple(visual.weights[index])
        new_index = unique_verts.get((coord, weights, is_back), None)

        if new_index is None:
            mesh.verts.new(coord)
            remap_verts[index] = remap_index
            unique_verts[(coord, weights, is_back)] = remap_index
            remap_index += 1

        else:
            remap_verts[index] = new_index

    return remap_verts


def create_vertices(visual, mesh, back_side):
    if visual.weights:
        remap_vertices = create_skinned_vertices(visual, mesh, back_side)
    else:
        remap_vertices = create_static_vertices(visual, mesh, back_side)

    mesh.verts.ensure_lookup_table()
    mesh.verts.index_update()

    return remap_vertices


def create_faces_new(visual, mesh, remap_vertices, norm_fun):
    remap_loops = []
    custom_normals = []

    # create triangles
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

            normal_1 = visual.normals[triangle[0]]
            normal_2 = visual.normals[triangle[1]]
            normal_3 = visual.normals[triangle[2]]

            custom_normals.extend((
                norm_fun(normal_1),
                norm_fun(normal_2),
                norm_fun(normal_3)
            ))
            remap_loops.extend(triangle)

        except ValueError:    # face already exists
            pass

    mesh.faces.ensure_lookup_table()

    # import uvs and vertex colors
    current_loop = 0
    uv_layer = mesh.loops.layers.uv.new('Texture')

    if visual.uvs_lmap:    # light maps
        hemi_vertex_color = mesh.loops.layers.color.new('Hemi')
        lmap_uv_layer = mesh.loops.layers.uv.new('Light Map')
        for face in mesh.faces:
            for loop in face.loops:
                index = remap_loops[current_loop]
                loop[uv_layer].uv = visual.uvs[index]
                loop[lmap_uv_layer].uv = visual.uvs_lmap[index]
                # hemi vertex color
                hemi = visual.hemi[index]
                hemi_loop = loop[hemi_vertex_color]
                hemi_loop[0 : 3] = hemi, hemi, hemi
                current_loop += 1

    elif visual.light:    # vertex colors
        hemi_vertex_color = mesh.loops.layers.color.new('Hemi')
        sun_vertex_color = mesh.loops.layers.color.new('Sun')
        light_vertex_color = mesh.loops.layers.color.new('Light')
        for face in mesh.faces:
            for loop in face.loops:
                index = remap_loops[current_loop]
                loop[uv_layer].uv = visual.uvs[index]
                # hemi vertex color
                hemi = visual.hemi[index]
                hemi_loop = loop[hemi_vertex_color]
                hemi_loop[0 : 3] = hemi, hemi, hemi
                # light vertex color
                light = visual.light[index]
                light_loop = loop[light_vertex_color]
                light_loop[0 : 3] = light
                # sun vertex color
                sun = visual.sun[index]
                sun_loop = loop[sun_vertex_color]
                sun_loop[0 : 3] = sun, sun, sun
                current_loop += 1

    else:
        if visual.hemi:    # trees
            hemi_vertex_color = mesh.loops.layers.color.new('Hemi')
            for face in mesh.faces:
                for loop in face.loops:
                    index = remap_loops[current_loop]
                    loop[uv_layer].uv = visual.uvs[index]
                    # hemi vertex color
                    hemi = visual.hemi[index]
                    hemi_loop = loop[hemi_vertex_color]
                    hemi_loop[0 : 3] = hemi, hemi, hemi
                    current_loop += 1
        else:    # ogf file
            for face in mesh.faces:
                for loop in face.loops:
                    index = remap_loops[current_loop]
                    loop[uv_layer].uv = visual.uvs[index]
                    current_loop += 1

    return custom_normals


def create_faces_old(visual, mesh, remap_vertices, norm_fun):
    remap_loops = []
    custom_normals = []

    # create triangles
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

                normal_1 = visual.normals[triangle[0]]
                normal_2 = visual.normals[triangle[1]]
                normal_3 = visual.normals[triangle[2]]

                custom_normals.extend((
                    norm_fun(normal_1),
                    norm_fun(normal_2),
                    norm_fun(normal_3)
                ))
                remap_loops.extend(triangle)

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

                remap_loops.extend(triangle)

            except ValueError:    # face already exists
                pass

    mesh.faces.ensure_lookup_table()

    # import uvs and vertex colors
    current_loop = 0
    uv_layer = mesh.loops.layers.uv.new('Texture')

    # light maps
    if visual.uvs_lmap:
        lmap_uv_layer = mesh.loops.layers.uv.new('Light Map')
        for face in mesh.faces:
            for loop in face.loops:
                index = remap_loops[current_loop]
                loop[uv_layer].uv = visual.uvs[index]
                loop[lmap_uv_layer].uv = visual.uvs_lmap[index]
                current_loop += 1

    # vertex colors
    elif visual.light:
        light_vertex_color = mesh.loops.layers.color.new('Light')
        for face in mesh.faces:
            for loop in face.loops:
                index = remap_loops[current_loop]
                loop[uv_layer].uv = visual.uvs[index]
                # light vertex color
                light = visual.light[index]
                light_loop = loop[light_vertex_color]
                light_loop[0 : 3] = light
                current_loop += 1

    else:
        for face in mesh.faces:
            for loop in face.loops:
                index = remap_loops[current_loop]
                loop[uv_layer].uv = visual.uvs[index]
                current_loop += 1

    return custom_normals


def create_visual(visual, lvl=None, geometry_key=None):
    vert_normals = get_vert_normals(visual)
    back_side = get_back_side(vert_normals)

    mesh = bmesh.new()

    remap_vertices = create_vertices(visual, mesh, back_side)

    # search convert normal function
    if visual.vb_index is None:
        convert_normal_fun = utility.convert_float_normal

    else:
        if lvl.vertex_buffers[visual.vb_index].float_normals:
            convert_normal_fun = utility.convert_float_normal
        else:
            convert_normal_fun = utility.convert_normal

    # import triangles
    is_new_format = False
    if lvl:
        if lvl.xrlc_version >= level.fmt.VERSION_11:
            is_new_format = True
    else:
        if visual.format_version == fmt.FORMAT_VERSION_4:
            is_new_format = True

    if is_new_format:
        custom_normals = create_faces_new(
            visual,
            mesh,
            remap_vertices,
            convert_normal_fun
        )
    else:
        custom_normals = create_faces_old(
            visual,
            mesh,
            remap_vertices,
            convert_normal_fun
        )

    # create mesh
    bpy_mesh = bpy.data.meshes.new(visual.name)
    bpy_mesh.use_auto_smooth = True
    bpy_mesh.auto_smooth_angle = math.pi

    # append material
    if lvl:
        material.assign_level_material(bpy_mesh, visual, lvl)

        # add geometry key
        lvl.loaded_geometry[geometry_key] = bpy_mesh

    else:
        bpy_mesh.materials.append(visual.bpy_material)

    # assign texture layer in blender 2.7x
    if not utils.version.IS_28:
        if lvl:
            bpy_image = lvl.images[visual.shader_id]
        else:
            bpy_image = visual.bpy_image

        texture_layer = mesh.faces.layers.tex.new('Texture')
        for face in mesh.faces:
            face[texture_layer].image = bpy_image

    # convert to bpy-mesh
    mesh.normal_update()
    mesh.to_mesh(bpy_mesh)

    # set custom normals
    if custom_normals:
        bpy_mesh.normals_split_custom_set(custom_normals)

    # create object
    bpy_object = utils.create_object(visual.name, bpy_mesh)

    # assign vertex weights
    assign_visual_vertex_weights(visual, bpy_object, remap_vertices)

    return bpy_object
