# standart modules
import math

# blender modules
import bpy
import bmesh
import mathutils

# addon modules
from . import base_bone
from ... import utils
from ... import formats


class _BoneShapeEditHelper(base_bone.AbstractBoneEditHelper):
    def draw(self, layout, context):    # pragma: no cover
        if self.is_active(context):
            layout.operator(XRAY_OT_apply_shape.bl_idname, icon='FILE_TICK')

            col = layout.column(align=True)

            hobj, bone = HELPER.get_target()
            shape_type = bone.xray.shape.type

            op = col.operator(
                XRAY_OT_fit_shape.bl_idname,
                text='Fit Shape',
                icon=utils.version.get_icon('BBOX')
            )
            op.mode = 'FIT'

            if shape_type in ('1', '3'):    # box, cylinder
                op = col.operator(
                    XRAY_OT_fit_shape.bl_idname,
                    text='Axis Align Bounding Box',
                    icon=utils.version.get_icon('BBOX')
                )
                op.mode = 'AABB'

                op = col.operator(
                    XRAY_OT_fit_shape.bl_idname,
                    text='Orient Bounding Box',
                    icon=utils.version.get_icon('BBOX')
                )
                op.mode = 'OBB'

            super().draw(layout, context)
            return

        layout.operator(XRAY_OT_edit_shape.bl_idname, text='Edit Shape')

    def _create_helper(self, name):
        mesh = bpy.data.meshes.new(name=name)
        return bpy.data.objects.new(name, mesh)

    def _delete_helper(self, helper):
        mesh = helper.data
        super()._delete_helper(helper)
        bpy.data.meshes.remove(mesh)

    def _update_helper(self, helper, target):
        bone = target
        shape_type = bone.xray.shape.type
        if shape_type == '0':
            self.deactivate()
            return

        super()._update_helper(helper, target)
        mesh = _create_bmesh(shape_type)
        mesh.to_mesh(helper.data)

        mat = bone_matrix(bone)
        helper.matrix_local = mat

        vscale = mat.to_scale()
        if not (vscale.x and vscale.y and vscale.z):
            bpy.ops.io_scene_xray.edit_bone_shape_fit()


HELPER = _BoneShapeEditHelper('bone-shape-edit')


def _create_bmesh(shape_type):
    mesh = bmesh.new()
    if shape_type == '1':
        bmesh.ops.create_cube(mesh, size=2)
    elif shape_type == '2':
        utils.version.create_bmesh_icosphere(mesh)
    elif shape_type == '3':
        utils.version.create_bmesh_cone(mesh, segments=16)
    else:
        raise AssertionError('unsupported bone shape type: ' + shape_type)
    return mesh


class XRAY_OT_edit_shape(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.edit_bone_shape'
    bl_label = 'Edit Bone Shape'
    bl_description = 'Create a helper object that can be ' \
        'used for adjusting bone shape'

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_ARMATURE':
            return False
        bone = context.active_bone
        return bone and (bone.xray.shape.type not in ('0', '4')) and \
            not HELPER.is_active(context)

    def execute(self, context):
        target = context.active_object.data.bones[context.active_bone.name]
        HELPER.activate(target)
        return {'FINISHED'}


def bone_matrix(bone):
    xsh = bone.xray.shape
    global pose_bone
    pose_bone = bpy.context.active_object.pose.bones[bone.name]
    multiply = utils.version.get_multiply()
    mat = multiply(
        pose_bone.matrix,
        mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
    )
    mat = multiply(mat, xsh.get_matrix_basis())
    if xsh.type == '1':  # box
        mat = multiply(mat, mathutils.Matrix.Scale(-1, 4, (0, 0, 1)))
        mat = multiply(mat, utils.bone.convert_vector_to_matrix(xsh.box_hsz))
    elif xsh.type == '2':  # sphere
        mat = multiply(mat, utils.bone.convert_vector_to_matrix((xsh.sph_rad, xsh.sph_rad, xsh.sph_rad)))
    elif xsh.type == '3':  # cylinder
        mat = multiply(mat, formats.motions.const.MATRIX_BONE_INVERTED)
        mat = multiply(
            mat,
            utils.bone.convert_vector_to_matrix((
                xsh.cyl_rad,
                xsh.cyl_rad,
                xsh.cyl_hgh * 0.5
            ))
        )
    else:
        raise AssertionError('unsupported bone shape type: ' + xsh.type)
    return mat


def maxabs(*args):
    result = 0
    for arg in args:
        result = max(result, abs(arg))
    return result


def apply_shape(bone, shape_matrix):
    xsh = bone.xray.shape
    multiply = utils.version.get_multiply()
    mat = multiply(
        multiply(
            pose_bone.matrix,
            mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
        ).inverted(),
        shape_matrix
    )
    if xsh.type == '1':  # box
        mat = multiply(mat, mathutils.Matrix.Scale(-1, 4, (0, 0, 1)))
        xsh.box_trn = mat.to_translation().to_tuple()
        scale = mat.to_scale()
        if not scale.length:
            return
        xsh.box_hsz = scale.to_tuple()
        mrt = multiply(mat, utils.bone.convert_vector_to_matrix(scale).inverted()).to_3x3().transposed()
        for index in range(3):
            xsh.box_rot[index * 3 : index * 3 + 3] = mrt[index].to_tuple()
    elif xsh.type == '2':  # sphere
        scale = mat.to_scale()
        if not scale.length:
            return
        xsh.sph_pos = mat.to_translation().to_tuple()
        xsh.sph_rad = maxabs(*scale)
    elif xsh.type == '3':  # cylinder
        xsh.cyl_pos = mat.to_translation().to_tuple()
        vscale = mat.to_scale()
        if not vscale.length:
            return
        xsh.cyl_hgh = abs(vscale[2]) * 2
        xsh.cyl_rad = maxabs(vscale[0], vscale[1])
        mat3 = mat.to_3x3()
        mscale = mathutils.Matrix.Identity(3)
        for axis in range(3):
            mscale[axis][axis] = 1 / vscale[axis]
        mat3 = multiply(mat3, mscale)
        qrot = mat3.transposed().to_quaternion().inverted()
        vrot = multiply(qrot, mathutils.Vector((0, 0, 1)))
        xsh.cyl_dir = vrot.to_tuple()
    else:
        raise AssertionError('unsupported shape type: ' + xsh.type)
    xsh.set_curver()


class XRAY_OT_apply_shape(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.edit_bone_shape_apply'
    bl_label = 'Apply Shape'
    bl_options = {'UNDO'}

    def execute(self, context):
        hobj, bone = HELPER.get_target()
        apply_shape(bone, hobj.matrix_local)
        for obj in bpy.data.objects:
            if obj.data == bone.id_data:
                utils.version.set_active_object(obj)
                break
        HELPER.deactivate()
        if utils.version.IS_28:
            bpy.context.view_layer.update()
        else:
            bpy.context.scene.update()
        return {'FINISHED'}


class XRAY_OT_fit_shape(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.edit_bone_shape_fit'
    bl_label = 'Fit Shape'
    bl_options = {'UNDO'}

    mode = bpy.props.EnumProperty(
        name='Mode',
        default='FIT',
        items=(
            ('FIT', 'Fit', 'Fit shape without rotation'),
            ('AABB', 'Axis Align Bounding Box', ''),
            ('OBB', 'Orient Bounding Box', '')
        )
    )

    def execute(self, context):
        def vfunc(vtx_a, vtx_b, func):
            vtx_a.x = func(vtx_a.x, vtx_b.x)
            vtx_a.y = func(vtx_a.y, vtx_b.y)
            vtx_a.z = func(vtx_a.z, vtx_b.z)

        hobj, bone = HELPER.get_target()

        if self.mode == 'AABB':
            matrix = mathutils.Matrix.Identity(4)
            matrix_inverted = matrix
        else:
            matrix = hobj.matrix_local
            matrix_inverted = matrix
            try:
                matrix_inverted = matrix.inverted()
            except ValueError:
                matrix = mathutils.Matrix.Identity(4)
                matrix_inverted = matrix

        hobj.scale = (1, 1, 1)  # ugly: force delayed refresh 3d-view
        vmin = mathutils.Vector((+math.inf, +math.inf, +math.inf))
        vmax = mathutils.Vector((-math.inf, -math.inf, -math.inf))
        xsh = bone.xray.shape
        multiply = utils.version.get_multiply()

        if xsh.type == '1':    # box
            obb_mat = utils.bone.get_obb(bone, False)

            if obb_mat and self.mode == 'OBB':
                hobj.matrix_local = obb_mat

            else:

                # generate aabb
                for vtx in utils.bone.bone_vertices(bone):
                    vtx = multiply(matrix_inverted, vtx)
                    vfunc(vmin, vtx, min)
                    vfunc(vmax, vtx, max)

                if vmax.x > vmin.x:
                    vcenter = (vmax + vmin) / 2
                    vscale = (vmax - vmin) / 2
                    hobj.matrix_local = multiply(
                        matrix,
                        mathutils.Matrix.Translation(vcenter),
                        utils.bone.convert_vector_to_matrix(vscale)
                    )

        else:
            vertices = []
            for vtx in utils.bone.bone_vertices(bone):
                vtx = multiply(matrix_inverted, vtx)
                vfunc(vmin, vtx, min)
                vfunc(vmax, vtx, max)
                vertices.append(vtx)

            if vmax.x > vmin.x:
                vcenter = (vmax + vmin) / 2
                radius = 0

                if xsh.type == '2':    # sphere
                    for vtx in vertices:
                        radius = max(radius, (vtx - vcenter).length)
                    hobj.matrix_local = multiply(
                        matrix,
                        mathutils.Matrix.Translation(vcenter),
                        utils.bone.convert_vector_to_matrix((radius, radius, radius))
                    )

                elif xsh.type == '3':    # cylinder
                    obb_mat = utils.bone.get_obb(bone, True)

                    if obb_mat and self.mode == 'OBB':
                        hobj.matrix_local = obb_mat

                    else:

                        # generate aabb
                        for vtx in vertices:
                            radius = max(radius, (vtx - vcenter).xy.length)
                        hobj.matrix_local = multiply(
                            matrix,
                            mathutils.Matrix.Translation(vcenter),
                            utils.bone.convert_vector_to_matrix((radius, radius, (vmax.z - vmin.z) * 0.5))
                        )

                else:
                    raise AssertionError('unsupported shape type: ' + xsh.type)

        if utils.version.IS_28:
            bpy.context.view_layer.update()
        else:
            bpy.context.scene.update()

        return {'FINISHED'}


classes = (
    XRAY_OT_edit_shape,
    XRAY_OT_apply_shape,
    XRAY_OT_fit_shape
)


def register():
    utils.version.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
