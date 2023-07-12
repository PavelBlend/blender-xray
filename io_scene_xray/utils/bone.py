# blender modules
import bpy
import bmesh
import mathutils
import numpy

# addon modules
from . import mesh
from . import version
from .. import log


def is_exportable_bone(bpy_bone):
    return bpy_bone.xray.exportable


def find_bone_exportable_parent(bpy_bone):
    result = bpy_bone.parent
    while (result is not None) and not is_exportable_bone(result):
        result = result.parent
    return result


def reset_pose_bone_transforms(armature_object):
    for bone in armature_object.pose.bones:
        bone.location = (0, 0, 0)
        bone.rotation_euler = (0, 0, 0)
        bone.rotation_quaternion = (1, 0, 0, 0)
        bone.scale = (1, 1, 1)


def get_ode_ik_limits(value_1, value_2):
    # swap special for ODE
    min_value = min(-value_1, -value_2)
    max_value = max(-value_1, -value_2)
    return min_value, max_value


def safe_assign_enum_property(bone_name, obj, prop_name, value, desc, custom):
    if value < custom:
        setattr(obj, prop_name, str(value))
    else:
        setattr(obj, prop_name, str(custom))
        setattr(obj, prop_name + '_custom_id', value)
        log.warn(
            desc,
            bone=bone_name,
            value=value
        )


def get_bone_prop(xray, prop_name, custom):
    value = int(getattr(xray, prop_name))
    if value == custom:
        value = getattr(xray, prop_name + '_custom_id')
    return value


def convert_vector_to_matrix(vector):
    matrix = mathutils.Matrix.Identity(4)
    for i, val in enumerate(vector):
        matrix[i][i] = val
    return matrix


def generate_obb(verts, for_cylinder):
    # generate orient bounding box
    # code adapted from here:
    # https://gist.github.com/iyadahmed/8874b92c27dee9d3ca63ab86bfc76295

    cov_mat = numpy.cov(verts, rowvar=False, bias=True)
    eig_vals, eig_vecs = numpy.linalg.eigh(cov_mat)

    change_of_basis_mat = eig_vecs
    inv_change_of_basis_mat = numpy.linalg.inv(change_of_basis_mat)

    aligned = verts.dot(inv_change_of_basis_mat.T)

    bbox_min = aligned.min(axis=0)
    bbox_max = aligned.max(axis=0)

    center = (bbox_max + bbox_min) / 2
    center_world = center.dot(change_of_basis_mat.T)
    scale = (bbox_max - bbox_min) / 2

    if for_cylinder:
        radius = max(scale[0], scale[1])
        scale[0] = radius
        scale[1] = radius

    mat_loc = mathutils.Matrix.Translation(center_world)
    mat_rot = mathutils.Matrix(change_of_basis_mat).to_4x4()
    mat_scl = version.multiply(
        mathutils.Matrix.Scale(abs(scale[0]), 4, (1, 0, 0)),
        mathutils.Matrix.Scale(abs(scale[1]), 4, (0, 1, 0)),
        mathutils.Matrix.Scale(abs(scale[2]), 4, (0, 0, 1))
    )
    inv_scl = mat_scl.inverted(None)
    if inv_scl is None:
        return

    mat_obb = version.multiply(mat_loc, mat_rot, mat_scl)

    return mat_obb


def _bone_objects(bone):
    arm = bone.id_data
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        group = obj.vertex_groups.get(bone.name, None)
        if group is None:
            continue
        for m in obj.modifiers:
            if m.type == 'ARMATURE' and m.object and m.object.data == arm:
                yield obj, group.index
                break


def bone_vertices(bone):
    verts = []
    for obj, vgi in _bone_objects(bone):
        bmsh = bmesh.new()
        if version.IS_28:
            bmsh.from_object(obj, bpy.context.view_layer.depsgraph)
        else:
            bmsh.from_object(obj, bpy.context.scene)
        layer_deform = bmsh.verts.layers.deform.verify()
        mesh.fix_ensure_lookup_table(bmsh.verts)
        for vtx in bmsh.verts:
            weight = vtx[layer_deform].get(vgi, 0)
            if weight:
                verts.append(tuple(vtx.co))
    return verts


def get_obb(bone, for_cylinder):
    # create convex hull mesh for obb generation
    bm = bmesh.new()
    for vert in bone_vertices(bone):
        bm.verts.new(vert)
    bm.verts.ensure_lookup_table()
    if len(bm.verts) >= 3:
        input_geom = bmesh.ops.convex_hull(bm, input=bm.verts)['geom']
    else:
        input_geom = bm.verts

    verts = []
    for elem in input_geom:
        if type(elem) == bmesh.types.BMVert:
            verts.extend(elem.co)

    # generate obb
    obb_mat = None
    if verts:
        coord_count = len(verts)
        verts_coord = numpy.empty(coord_count, dtype=numpy.float32)
        for index, coord in enumerate(verts):
            verts_coord[index] = coord
        verts_coord.shape = (coord_count // 3, 3)

        obb_mat = generate_obb(verts_coord, for_cylinder)

    return obb_mat
