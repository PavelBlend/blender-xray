# blender modules
import mathutils

# addon modules
from .. import fmt
from .... import rw
from .... import utils


MATRIX_BONE = mathutils.Matrix.Scale(-1, 4, (0, 0, 1)).freeze()


def _get_default_bone_bound():
    box_rot = (
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
        0.0, 0.0, 1.0
    )
    box_trn = (0.0, 0.0, 0.0)
    box_hsz = (0.0, 0.0, 0.0)
    return box_rot, box_trn, box_hsz


def _bone_mat_to_scale(bone_mat):
    bone_scale = bone_mat.to_scale()

    for axis in range(3):
        if not bone_scale[axis]:
            bone_scale[axis] = 0.0001

    return bone_scale


def _bone_mat_to_rotate(bone_mat, bone_scale, mul):
    scale_mat = utils.bone.convert_vector_to_matrix(bone_scale)
    mat_rot = mul(bone_mat, scale_mat.inverted()).to_3x3().transposed()

    box_rot = []
    for row in range(3):
        box_rot.extend(mat_rot[row].to_tuple())

    return box_rot


def _get_bone_half_size(bone_scale, scale):
    half_size = bone_scale * scale

    for axis in range(3):
        half_size[axis] = abs(half_size[axis])

    return half_size


def _get_bone_box(bone, bone_mat, scale, mul):
    local_mat = mul(bone.matrix_local, MATRIX_BONE)
    bone_mat = mul(local_mat.inverted(), bone_mat)
    bone_mat = mul(bone_mat, MATRIX_BONE)
    bone_scale = _bone_mat_to_scale(bone_mat)

    box_rot = _bone_mat_to_rotate(bone_mat, bone_scale, mul)
    box_trn = bone_mat.to_translation() * scale
    box_hsz = _get_bone_half_size(bone_scale, scale)

    return box_rot, box_trn, box_hsz


def _get_bone_bound(bone, scale, mul):
    vertices, _ = utils.bone.bone_vertices(bone)

    if len(vertices) > 3:
        # generate obb
        mat = utils.bone.get_obb(bone, False, 0.0)

        if not mat:
            # generate aabb
            mat = utils.bone.get_aabb(vertices)

        if mat:
            box_rot, box_trn, box_hsz = _get_bone_box(bone, mat, scale, mul)

        else:
            box_rot, box_trn, box_hsz = _get_default_bone_bound()

    else:
        box_rot, box_trn, box_hsz = _get_default_bone_bound()

    return box_rot, box_trn, box_hsz


def write_bone_names(bones, scale, ogf_writer):
    bones_writer = rw.write.PackedWriter()

    bones_count = len(bones)
    bones_writer.putf('<I', bones_count)

    multiply = utils.version.get_multiply()

    for bone, _ in bones:
        parent = utils.bone.find_bone_exportable_parent(bone)

        if parent:
            parent_name = parent.name
        else:
            parent_name = ''

        # bone bound
        box_rot, box_trn, box_hsz = _get_bone_bound(bone, scale, multiply)

        # write
        bones_writer.puts(bone.name)
        bones_writer.puts(parent_name)
        bones_writer.putf('<15f', *box_rot, *box_trn, *box_hsz)

    # write chunk
    ogf_writer.put(fmt.Chunks_v4.S_BONE_NAMES, bones_writer)


def reg_bone(bones, bones_map, bone, adv):
    bone_index = bones_map.get(bone, None)

    if bone_index is None:
        bone_index = len(bones)
        bones.append((bone, adv))
        bones_map[bone] = bone_index

    return bone_index
