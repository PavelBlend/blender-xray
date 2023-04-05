# blender modules
import bpy
import bmesh
import mathutils

# addon modules
from . import version


def convert_object_to_space_bmesh(
        bpy_obj,
        space_matrix,
        local=False,
        split_normals=False,
        mods=None
    ):

    mesh = bmesh.new()
    exportable_obj = bpy_obj
    temp_obj = None

    # set sharp edges by face smoothing
    if split_normals and version.has_set_normals_from_faces():
        temp_mesh = bpy_obj.data.copy()
        temp_obj = bpy_obj.copy()
        temp_obj.data = temp_mesh
        for polygon in temp_mesh.polygons:
            if polygon.use_smooth:
                continue
            for loop_index in polygon.loop_indices:
                loop = temp_mesh.loops[loop_index]
                edge = temp_mesh.edges[loop.edge_index]
                edge.use_edge_sharp = True
        version.link_object(temp_obj)
        bpy.ops.object.select_all(action='DESELECT')
        version.set_active_object(temp_obj)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.set_normals_from_faces()
        bpy.ops.object.mode_set(mode='OBJECT')
        exportable_obj = temp_obj

    # apply shape keys
    if exportable_obj.data.shape_keys:
        if not temp_obj:
            temp_mesh = exportable_obj.data.copy()
            temp_obj = exportable_obj.copy()
            temp_obj.data = temp_mesh
            version.link_object(temp_obj)
            version.set_active_object(temp_obj)
            exportable_obj = temp_obj
        temp_obj.shape_key_add(name='last_shape_key', from_mix=True)
        for shape_key in temp_mesh.shape_keys.key_blocks:
            temp_obj.shape_key_remove(shape_key)

    # apply modifiers
    if mods:
        if not temp_obj:
            temp_mesh = exportable_obj.data.copy()
            temp_obj = exportable_obj.copy()
            temp_obj.data = temp_mesh
            version.link_object(temp_obj)
            version.set_active_object(temp_obj)
            exportable_obj = temp_obj
        for mod in mods:
            bpy.ops.object.modifier_apply(modifier=mod.name)

    mesh.from_mesh(exportable_obj.data)

    # apply mesh transforms
    if local:
        mat = mathutils.Matrix()
    else:
        mat = bpy_obj.matrix_world

    mat = version.multiply(space_matrix.inverted(), mat)

    mesh.transform(mat)

    # flip normals
    need_flip = False
    for scale_component in mat.to_scale():
        if scale_component < 0:
            need_flip = not need_flip
    if need_flip:
        bmesh.ops.reverse_faces(mesh, faces=mesh.faces)

    fix_ensure_lookup_table(mesh.verts)

    # remove temp mesh object
    if temp_obj:
        bpy.data.objects.remove(temp_obj)
        bpy.data.meshes.remove(temp_mesh)

    return mesh


def fix_ensure_lookup_table(bm_sequence):
    if hasattr(bm_sequence, 'ensure_lookup_table'):
        bm_sequence.ensure_lookup_table()


def set_bound_coord(bound, current, compare_fun):
    bound.x = compare_fun(bound.x, current.x)
    bound.y = compare_fun(bound.y, current.y)
    bound.z = compare_fun(bound.z, current.z)


def calculate_mesh_bbox(verts, mat=mathutils.Matrix()):
    fix_ensure_lookup_table(verts)
    multiply = version.get_multiply()
    bbox_min = multiply(mat, verts[0].co).copy()
    bbox_max = bbox_min.copy()

    for vertex in verts:
        set_bound_coord(bbox_min, multiply(mat, vertex.co), min)
        set_bound_coord(bbox_max, multiply(mat, vertex.co), max)

    return bbox_min, bbox_max
