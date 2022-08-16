# blender modules
import bpy
import mathutils
import bmesh

# addon modules
from . import version
from .. import log


def convert_object_to_space_bmesh(bpy_obj, space_matrix, local=False, split_normals=False, mods=None):
    mesh = bmesh.new()
    temp_obj = None
    if split_normals and version.has_set_normals_from_faces():
        temp_mesh = bpy_obj.data.copy()
        temp_obj = bpy_obj.copy()
        temp_obj.data = temp_mesh
        # set sharp edges by face smoothing
        for polygon in temp_mesh.polygons:
            if polygon.use_smooth:
                continue
            for loop_index in polygon.loop_indices:
                loop = temp_mesh.loops[loop_index]
                edge = temp_mesh.edges[loop.edge_index]
                edge.use_edge_sharp = True
        version.link_object(temp_obj)
        version.set_active_object(temp_obj)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.set_normals_from_faces()
        bpy.ops.object.mode_set(mode='OBJECT')
        exportable_obj = temp_obj
    else:
        exportable_obj = bpy_obj
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
            temp_mesh = bpy_obj.data.copy()
            temp_obj = bpy_obj.copy()
            temp_obj.data = temp_mesh
            version.link_object(temp_obj)
            version.set_active_object(temp_obj)
            exportable_obj = temp_obj
        override = bpy.context.copy()
        override['active_object'] = temp_obj
        override['object'] = temp_obj
        for mod in mods:
            bpy.ops.object.modifier_apply(override, modifier=mod.name)
    mesh.from_mesh(exportable_obj.data)
    if local:
        mat = mathutils.Matrix()
    else:
        mat = bpy_obj.matrix_world
    mat = version.multiply(space_matrix.inverted(), mat)
    mesh.transform(mat)
    need_flip = False
    for scale_component in mat.to_scale():
        if scale_component < 0:
            need_flip = not need_flip
    if need_flip:
        bmesh.ops.reverse_faces(mesh, faces=mesh.faces)  # flip normals
    fix_ensure_lookup_table(mesh.verts)
    if temp_obj:
        bpy.data.objects.remove(temp_obj)
        bpy.data.meshes.remove(temp_mesh)
    return mesh


def fix_ensure_lookup_table(bmv):
    if hasattr(bmv, 'ensure_lookup_table'):
        bmv.ensure_lookup_table()


def calculate_mesh_bbox(verts, mat=mathutils.Matrix()):
    def vfunc(dst, src, func):
        dst.x = func(dst.x, src.x)
        dst.y = func(dst.y, src.y)
        dst.z = func(dst.z, src.z)

    multiply = version.get_multiply()
    fix_ensure_lookup_table(verts)
    _min = multiply(mat, verts[0].co).copy()
    _max = _min.copy()

    vs = []
    for vertex in verts:
        vfunc(_min, multiply(mat, vertex.co), min)
        vfunc(_max, multiply(mat, vertex.co), max)
        vs.append(_max)

    return _min, _max
