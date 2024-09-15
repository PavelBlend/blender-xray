# standart modules
import math

# blender modules
import bpy
import bmesh
import mathutils

# addon modules
from . import base
from ... import utils
from ... import text
from ... import formats


class _BoneShapeEditHelper:
    def __init__(self, name):
        base.__HELPERS__[name] = self
        self._name = utils.obj.HELPER_OBJECT_NAME_PREFIX + name

    def draw(self, layout, context):    # pragma: no cover
        def operator_if(op, **kwargs):
            if not op.poll():
                return None
            return layout.operator(
                op.idname(),
                **kwargs,
            )

        if self.is_active(context):
            operator_if(
                bpy.ops.io_scene_xray.edit_bone_shape_apply,
                text=text.get_iface(text.iface.apply_shape),
                icon='FILE_TICK'
            )

            _, bone = self.get_helper(context)
            shape_type = bone.xray.shape.type

            op = operator_if(
                bpy.ops.io_scene_xray.edit_bone_shape_fit,
                text=text.get_iface(text.iface.fit_shape),
                icon=utils.version.get_icon('BBOX')
            )

            if op and shape_type in ('1', '3'):    # box, cylinder
                op = layout.operator(
                    op.bl_rna.identifier,
                    text=text.get_iface(text.iface.aabb),
                    icon=utils.version.get_icon('BBOX')
                )
                op.mode = 'AABB'

                op = layout.operator(
                    op.bl_rna.identifier,
                    text=text.get_iface(text.iface.obb),
                    icon=utils.version.get_icon('BBOX')
                )
                op.mode = 'OBB'

            layout.operator(
                base.XRAY_OT_edit_cancel.bl_idname,
                text=text.get_iface(text.iface.cancel),
                icon='X'
            )
            return

        layout.operator(
            XRAY_OT_edit_shape.bl_idname,
            text=text.get_iface(text.iface.edit_shape)
        )

    def is_active(self, context=bpy.context):
        return self.get_helper(context)[0] is not None

    def get_helper(self, context):
        obj = context.active_object
        if (obj is None) or (obj.pose is None):
            return None, None
        helper = obj.pose.bones.get(self._name)
        if helper is None:
            return None, None
        return helper, obj.data.bones[helper.parent.name]

    def bone_to_target(self, bone):
        if bone.name == self._name:
            return bone.parent
        return bone

    def activate(self, context):
        bone = context.active_bone
        armature = bone.id_data
        target_name = bone.name
        with utils.version.using_mode('EDIT'):
            edit_bones = armature.edit_bones
            target_edit = edit_bones[target_name]
            helper = edit_bones.get(self._name)
            if helper is None:
                helper = edit_bones.new(self._name)
                helper.show_wire = True
            helper.parent = target_edit
            for key in ('head', 'tail', 'roll'):
                setattr(helper, key, getattr(target_edit, key))
        bone = armature.bones[self._name]
        bone.xray.exportable = False
        armature.bones.active = bone
        armature.bones[target_name].select = False
        self.update(context)
    
    def update(self, context):
        helper, target = self.get_helper(context)
        if helper is None:
            return

        shape_type = target.xray.shape.type
        key = self._name + '--' + shape_type
        obj = bpy.data.objects.get(key)
        if obj is None:
            mesh = bpy.data.meshes.new(key)
            bmesh = _create_bmesh(shape_type)
            bmesh.to_mesh(mesh)
            obj = bpy.data.objects.new(key, mesh)
        helper.custom_shape = obj
        helper.use_custom_shape_bone_size = False

        mat = bone_matrix(target)
        helper.matrix = mat

        scale = mat.to_scale()
        if not (scale.x and scale.y and scale.z):
            bpy.ops.io_scene_xray.edit_bone_shape_fit()

    def deactivate(self):
        _, target = self.get_helper(bpy.context)
        target_name = target.name
        armature = target.id_data
        edit_bones = armature.edit_bones
        with utils.version.using_mode('EDIT'):
            edit_bones.remove(edit_bones[self._name])
        armature.bones.active = armature.bones[target_name]


HELPER = _BoneShapeEditHelper('bone-shape-edit')


def _create_bmesh(shape_type):
    mesh = bmesh.new()

    if shape_type == '1':
        bmesh.ops.create_cube(mesh, size=2)

    elif shape_type == '2':
        utils.version.create_bmesh_icosphere(mesh)

    elif shape_type == '3':
        utils.version.create_bmesh_cone(mesh, segments=16)

    return mesh


class XRAY_OT_edit_shape(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.edit_bone_shape'
    bl_label = 'Edit Bone Shape'
    bl_description = 'Create a helper object that can be ' \
        'used for adjusting bone shape'

    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_ARMATURE':
            return False

        bone = context.active_bone
        if not bone:
            return False

        # is not "None" or "Custom" shape type
        has_shape = bone.xray.shape.type not in ('0', '4')

        return has_shape and not HELPER.is_active(context)

    def execute(self, context):
        HELPER.activate(context)
        return {'FINISHED'}


def bone_matrix(bone):
    xsh = bone.xray.shape
    pose_bone = bpy.context.active_object.pose.bones[bone.name]
    multiply = utils.version.get_multiply()
    mat = multiply(
        pose_bone.matrix,
        mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
    )
    mat = multiply(mat, xsh.get_matrix_basis())

    if xsh.type == '1':    # box
        mat = multiply(mat, mathutils.Matrix.Scale(-1, 4, (0, 0, 1)))
        mat = multiply(mat, utils.bone.convert_vector_to_matrix(xsh.box_hsz))

    elif xsh.type == '2':    # sphere
        mat = multiply(
            mat,
            utils.bone.convert_vector_to_matrix((
                xsh.sph_rad,
                xsh.sph_rad,
                xsh.sph_rad
            ))
        )

    elif xsh.type == '3':    # cylinder
        mat = multiply(mat, formats.motions.const.MATRIX_BONE_INVERTED)
        mat = multiply(
            mat,
            utils.bone.convert_vector_to_matrix((
                xsh.cyl_rad,
                xsh.cyl_rad,
                xsh.cyl_hgh * 0.5
            ))
        )

    return mat


def maxabs(*args):
    result = 0
    for arg in args:
        result = max(result, abs(arg))
    return result


def apply_shape(bone, shape_matrix):
    xsh = bone.xray.shape
    multiply = utils.version.get_multiply()
    pose_bone = bpy.context.active_object.pose.bones[bone.name]
    mat = multiply(
        multiply(
            pose_bone.matrix,
            mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
        ).inverted(),
        shape_matrix
    )

    if xsh.type == '1':    # box
        mat = multiply(mat, mathutils.Matrix.Scale(-1, 4, (0, 0, 1)))
        xsh.box_trn = mat.to_translation().to_tuple()
        scale = mat.to_scale()
        if not scale.length:
            return
        xsh.box_hsz = scale.to_tuple()
        mrt = multiply(
            mat,
            utils.bone.convert_vector_to_matrix(scale).inverted()
        ).to_3x3().transposed()

        for index in range(3):
            xsh.box_rot[index * 3 : index * 3 + 3] = mrt[index].to_tuple()

    elif xsh.type == '2':    # sphere
        scale = mat.to_scale()
        if not scale.length:
            return
        xsh.sph_pos = mat.to_translation().to_tuple()
        xsh.sph_rad = maxabs(*scale)

    elif xsh.type == '3':    # cylinder
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
    bl_label = text.iface.apply_shape
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        _, bone = HELPER.get_helper(context)
        return bone.xray.shape.type in ('1', '2', '3')

    def execute(self, context):
        hbone, bone = HELPER.get_helper(context)
        apply_shape(bone, hbone.matrix)
        HELPER.deactivate()
        if utils.version.IS_28:
            bpy.context.view_layer.update()
        else:
            bpy.context.scene.update()
        return {'FINISHED'}


class XRAY_OT_fit_shape(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.edit_bone_shape_fit'
    bl_label = text.iface.fit_shape
    bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.EnumProperty(
        name='Mode',
        default='FIT',
        items=(
            ('FIT', 'Fit', 'Fit shape without rotation'),
            ('AABB', 'Axis Align Bounding Box', ''),
            ('OBB', 'Orient Bounding Box', '')
        )
    )
    min_weight = bpy.props.FloatProperty(
        default=0.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
        name='Min Weight'
    )

    @classmethod
    def poll(cls, context):
        _, bone = HELPER.get_helper(context)
        return bone.xray.shape.type in ('1', '2', '3')

    def draw(self, context):    # pragma: no cover
        self.layout.prop(self, 'mode')
        self.layout.prop(self, 'min_weight')

    def execute(self, context):
        def vfunc(vtx_a, vtx_b, func):
            vtx_a.x = func(vtx_a.x, vtx_b.x)
            vtx_a.y = func(vtx_a.y, vtx_b.y)
            vtx_a.z = func(vtx_a.z, vtx_b.z)

        multiply = utils.version.get_multiply()

        hbone, bone = HELPER.get_helper(context)
        obj = hbone.id_data

        def set_matrix(matrix):
            hbone.matrix =  multiply(obj.matrix_world.inverted(), matrix)

        if self.mode == 'AABB':
            matrix = mathutils.Matrix.Identity(4)
            matrix_inverted = matrix
        else:
            matrix = multiply(obj.matrix_world, hbone.matrix)
            matrix_inverted = matrix
            try:
                matrix_inverted = matrix.inverted()
            except ValueError:
                matrix = mathutils.Matrix.Identity(4)
                matrix_inverted = matrix

        vmin = mathutils.Vector((+math.inf, +math.inf, +math.inf))
        vmax = mathutils.Vector((-math.inf, -math.inf, -math.inf))
        stype = bone.xray.shape.type

        if stype == '1':    # box
            obb_mat = utils.bone.get_obb(bone, False, self.min_weight, in_world_coordinates=True)

            if obb_mat and self.mode == 'OBB':
                set_matrix(obb_mat)

            else:

                # generate aabb
                verts, weights = utils.bone.bone_vertices(bone, in_world_coordinates=True)
                for index, vtx in enumerate(verts):
                    weight = weights[index]
                    if weight >= self.min_weight:
                        vtx = multiply(matrix_inverted, vtx)
                        vfunc(vmin, vtx, min)
                        vfunc(vmax, vtx, max)

                if vmax.x > vmin.x:
                    vcenter = (vmax + vmin) / 2
                    vscale = (vmax - vmin) / 2
                    set_matrix(multiply(
                        matrix,
                        mathutils.Matrix.Translation(vcenter),
                        utils.bone.convert_vector_to_matrix(vscale)
                    ))

        else:
            vertices = []
            verts, weights = utils.bone.bone_vertices(bone, in_world_coordinates=True)
            for index, vtx in enumerate(verts):
                weight = weights[index]
                if weight >= self.min_weight:
                    vtx = multiply(matrix_inverted, vtx)
                    vfunc(vmin, vtx, min)
                    vfunc(vmax, vtx, max)
                    vertices.append(vtx)

            if vmax.x > vmin.x:
                vcenter = (vmax + vmin) / 2
                radius = 0

                if stype == '2':    # sphere
                    for vtx in vertices:
                        radius = max(radius, (vtx - vcenter).length)
                    set_matrix(multiply(
                        matrix,
                        mathutils.Matrix.Translation(vcenter),
                        utils.bone.convert_vector_to_matrix((
                            radius,
                            radius,
                            radius
                        ))
                    ))

                elif stype == '3':    # cylinder
                    obb_mat = utils.bone.get_obb(bone, True, self.min_weight, in_world_coordinates=True)

                    if obb_mat and self.mode == 'OBB':
                        set_matrix(obb_mat)

                    else:

                        # generate aabb
                        for vtx in vertices:
                            radius = max(radius, (vtx - vcenter).xy.length)
                        set_matrix(multiply(
                            matrix,
                            mathutils.Matrix.Translation(vcenter),
                            utils.bone.convert_vector_to_matrix((
                                radius,
                                radius,
                                (vmax.z - vmin.z) * 0.5
                            ))
                        ))

                else:
                    raise AssertionError('unsupported shape type: ' + stype)

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
    utils.version.register_classes(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
