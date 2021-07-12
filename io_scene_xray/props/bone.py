import math

import bpy
import bgl
import mathutils
import gpu

from . import utils
from ..ops import joint_limits
from ..edit_helpers.bone_shape import HELPER as seh
from ..version_utils import assign_props, IS_28, multiply, get_multiply


shape_properties = {
    'type': bpy.props.EnumProperty(
        items=(
            ('0', 'None', ''),
            ('1', 'Box', ''),
            ('2', 'Sphere', ''),
            ('3', 'Cylinder', '')
        ),
        update=lambda self, ctx: seh.update(),
    ),
    'flags': bpy.props.IntProperty(),
    'flags_nopickable': utils.gen_flag_prop(mask=0x1),
    'flags_removeafterbreak': utils.gen_flag_prop(mask=0x2),
    'flags_nophysics': utils.gen_flag_prop(mask=0x4),
    'flags_nofogcollider': utils.gen_flag_prop(mask=0x8),
    'box_rot': bpy.props.FloatVectorProperty(size=9),
    'box_trn': bpy.props.FloatVectorProperty(),
    'box_hsz': bpy.props.FloatVectorProperty(),
    'sph_pos': bpy.props.FloatVectorProperty(),
    'sph_rad': bpy.props.FloatProperty(),
    'cyl_pos': bpy.props.FloatVectorProperty(),
    'cyl_dir': bpy.props.FloatVectorProperty(),
    'cyl_hgh': bpy.props.FloatProperty(),
    'cyl_rad': bpy.props.FloatProperty(),
    'version_data': bpy.props.IntProperty()
}


class ShapeProperties(bpy.types.PropertyGroup):
    _CURVER_DATA = 1

    if not IS_28:
        for prop_name, prop_value in shape_properties.items():
            exec('{0} = shape_properties.get("{0}")'.format(prop_name))

    def check_version_different(self):
        def iszero(vec):
            return not any(v for v in vec)

        if self.version_data == self._CURVER_DATA:
            return 0
        if self.type == '0':  # none
            return 0
        elif self.type == '1':  # box
            if iszero(self.box_trn) and iszero(self.box_rot) and iszero(self.box_hsz):
                return 0  # default shape
        elif self.type == '2':  # sphere
            if iszero(self.sph_pos) and not self.sph_rad:
                return 0  # default shape
        elif self.type == '3':  # cylinder
            if iszero(self.cyl_pos) \
                and iszero(self.cyl_dir) \
                and not self.cyl_rad \
                and not self.cyl_hgh:
                return 0  # default shape
        return 1 if self.version_data < self._CURVER_DATA else 2

    @staticmethod
    def fmt_version_different(res):
        return 'obsolete' if res == 1 else ('newest' if res == 2 else 'different')

    def set_curver(self):
        self.version_data = self._CURVER_DATA

    def get_matrix_basis(self) -> mathutils.Matrix:
        typ = self.type
        if typ == '1':  # box
            rot = self.box_rot
            return multiply(
                mathutils.Matrix.Translation(self.box_trn),
                mathutils.Matrix((rot[0:3], rot[3:6], rot[6:9])).transposed().to_4x4()
            )
        if typ == '2':  # sphere
            return mathutils.Matrix.Translation(self.sph_pos)
        if typ == '3':  # cylinder
            v_dir = mathutils.Vector(self.cyl_dir)
            q_rot = v_dir.rotation_difference((0, 1, 0))
            return multiply(
                mathutils.Matrix.Translation(self.cyl_pos),
                q_rot.to_matrix().transposed().to_4x4()
            )


break_properties = {
    'force': bpy.props.FloatProperty(),
    'torque': bpy.props.FloatProperty()
}


class BreakProperties(bpy.types.PropertyGroup):
    if not IS_28:
        for prop_name, prop_value in break_properties.items():
            exec('{0} = break_properties.get("{0}")'.format(prop_name))


ik_joint_properties = {
    'type': bpy.props.EnumProperty(items=(
        ('0', 'Rigid', ''),
        ('1', 'Cloth', ''),
        ('2', 'Joint', ''),
        ('3', 'Wheel', ''),
        ('4', 'None', ''),
        ('5', 'Slider', ''))
    ),
    'lim_x_min': bpy.props.FloatProperty(
        min=-math.pi, max=0, update=joint_limits.update_limit, subtype='ANGLE'
    ),
    'lim_x_max': bpy.props.FloatProperty(
        min=0, max=math.pi, update=joint_limits.update_limit, subtype='ANGLE'
    ),
    'lim_x_spr': bpy.props.FloatProperty(min=0),
    'lim_x_dmp': bpy.props.FloatProperty(min=0),
    'lim_y_min': bpy.props.FloatProperty(
        min=-math.pi, max=0, update=joint_limits.update_limit, subtype='ANGLE'
    ),
    'lim_y_max': bpy.props.FloatProperty(
        min=0, max=math.pi, update=joint_limits.update_limit, subtype='ANGLE'
    ),
    'lim_y_spr': bpy.props.FloatProperty(min=0),
    'lim_y_dmp': bpy.props.FloatProperty(min=0),
    'lim_z_min': bpy.props.FloatProperty(
        min=-math.pi, max=0, update=joint_limits.update_limit, subtype='ANGLE'
    ),
    'lim_z_max': bpy.props.FloatProperty(
        min=0, max=math.pi, update=joint_limits.update_limit, subtype='ANGLE'
    ),
    'lim_z_spr': bpy.props.FloatProperty(min=0),
    'lim_z_dmp': bpy.props.FloatProperty(min=0),
    'spring': bpy.props.FloatProperty(),
    'damping': bpy.props.FloatProperty(),
    'is_rigid': bpy.props.BoolProperty(get=lambda self: self.type == '0')
}


class IKJointProperties(bpy.types.PropertyGroup):
    if not IS_28:
        for prop_name, prop_value in ik_joint_properties.items():
            exec('{0} = ik_joint_properties.get("{0}")'.format(prop_name))


mass_properties = {
    'value': bpy.props.FloatProperty(name='Mass', precision=3),
    'center': bpy.props.FloatVectorProperty(name='Center of Mass', precision=3)
}

class MassProperties(bpy.types.PropertyGroup):
    if not IS_28:
        for prop_name, prop_value in mass_properties.items():
            exec('{0} = mass_properties.get("{0}")'.format(prop_name))


def set_ikflags_breakable(self, value):
    self.ikflags = self.ikflags | 0x1 if value else self.ikflags & ~0x1


xray_bone_properties = {
    'exportable': bpy.props.BoolProperty(default=True, description='Enable Bone to be exported'),
    'version': bpy.props.IntProperty(),
    'length': bpy.props.FloatProperty(name='Length'),
    'gamemtl': bpy.props.StringProperty(default='default_object'),
    'shape': bpy.props.PointerProperty(type=ShapeProperties),
    'ikflags': bpy.props.IntProperty(),
    'ikflags_breakable': bpy.props.BoolProperty(
        get=lambda self: self.ikflags & 0x1,
        set=set_ikflags_breakable,
        options={'SKIP_SAVE'}
    ),
    'ikjoint': bpy.props.PointerProperty(type=IKJointProperties),
    'breakf': bpy.props.PointerProperty(type=BreakProperties),
    'friction': bpy.props.FloatProperty(),
    'mass': bpy.props.PointerProperty(type=MassProperties)
}


class XRayBoneProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Bone

    if not IS_28:
        for prop_name, prop_value in xray_bone_properties.items():
            exec('{0} = xray_bone_properties.get("{0}")'.format(prop_name))

    def ondraw_postview(self, obj_arm, bone):
        # draw limits
        arm_xray = obj_arm.data.xray
        if IS_28:
            hide = obj_arm.hide_viewport
        else:
            hide = obj_arm.hide
        multiply = get_multiply()
        if not hide and arm_xray.display_bone_limits and \
                        bone.xray.exportable and obj_arm.mode == 'POSE':
            if bone.select and bone.xray.ikjoint.type in {'2', '3', '5'} and \
                    bpy.context.object.name == obj_arm.name:

                if IS_28:
                    from ..gpu_utils import draw_joint_limits
                    gpu.matrix.push()
                else:
                    from ..gl_utils import draw_joint_limits, matrix_to_buffer
                    bgl.glPushMatrix()
                    bgl.glEnable(bgl.GL_BLEND)
                mat_translate = mathutils.Matrix.Translation(obj_arm.pose.bones[bone.name].matrix.to_translation())
                mat_rotate = obj_arm.data.bones[bone.name].matrix_local.to_euler().to_matrix().to_4x4()
                if bone.parent:
                    mat_rotate_parent = obj_arm.pose.bones[bone.parent.name].matrix_basis.to_euler().to_matrix().to_4x4()
                else:
                    mat_rotate_parent = mathutils.Matrix()

                mat = multiply(
                    obj_arm.matrix_world,
                    mat_translate,
                    multiply(mat_rotate, mat_rotate_parent),
                    mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
                )
                if IS_28:
                    gpu.matrix.multiply_matrix(mat)
                else:
                    bgl.glMultMatrixf(matrix_to_buffer(mat.transposed()))

                pose_bone = obj_arm.pose.bones[bone.name]
                if pose_bone.rotation_mode == 'QUATERNION':
                    rotate = pose_bone.rotation_quaternion.to_euler('XYZ')
                else:
                    rotate = obj_arm.pose.bones[bone.name].rotation_euler

                ik = bone.xray.ikjoint

                if arm_xray.display_bone_limit_x:
                    draw_joint_limits(
                        rotate.x, ik.lim_x_min, ik.lim_x_max, 'X',
                        arm_xray.display_bone_limits_radius
                    )

                if arm_xray.display_bone_limit_y:
                    draw_joint_limits(
                        rotate.y, ik.lim_y_min, ik.lim_y_max, 'Y',
                        arm_xray.display_bone_limits_radius
                    )

                if arm_xray.display_bone_limit_z:
                    draw_joint_limits(
                        rotate.z, ik.lim_z_min, ik.lim_z_max, 'Z',
                        arm_xray.display_bone_limits_radius
                    )

                if IS_28:
                    gpu.matrix.pop()
                else:
                    bgl.glPopMatrix()

        # draw shapes
        if IS_28:
            arm_hide = obj_arm.hide_viewport
        else:
            arm_hide = obj_arm.hide
        if arm_hide or not obj_arm.data.xray.display_bone_shapes or \
                        not bone.xray.exportable or obj_arm.mode == 'EDIT':
            return

        if IS_28:
            if not obj_arm.name in bpy.context.view_layer.objects:
                return
        else:
            if not obj_arm.name in bpy.context.scene.objects:
                return
            visible_armature_object = False
            for layer_index, layer in enumerate(obj_arm.layers):
                scene_layer = bpy.context.scene.layers[layer_index]
                if scene_layer and layer:
                    visible_armature_object = True
                    break

            if not visible_armature_object:
                return

        from ..gl_utils import matrix_to_buffer, \
            draw_wire_cube, draw_wire_sphere, draw_wire_cylinder, draw_cross

        shape = self.shape
        if shape.type == '0':
            return
        if IS_28:
            from ..gpu_utils import draw_wire_cube, draw_wire_sphere, \
                draw_wire_cylinder, draw_cross
            if bpy.context.active_bone \
                and (bpy.context.active_bone.id_data == obj_arm.data) \
                and (bpy.context.active_bone.name == bone.name):
                color = (1.0, 0.0, 0.0, 0.7)
            else:
                color = (0.0, 0.0, 1.0, 0.5)
            gpu.matrix.push()
            try:
                mat = multiply(
                    obj_arm.matrix_world,
                    obj_arm.pose.bones[bone.name].matrix,
                    mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
                )
                bmat = mat
                mat = multiply(mat, shape.get_matrix_basis())
                gpu.matrix.multiply_matrix(mat)
                if shape.type == '1':  # box
                    draw_wire_cube(*shape.box_hsz, color)
                if shape.type == '2':  # sphere
                    draw_wire_sphere(shape.sph_rad, 16, color)
                if shape.type == '3':  # cylinder
                    draw_wire_cylinder(shape.cyl_rad, shape.cyl_hgh * 0.5, 16, color)
                gpu.matrix.pop()
                gpu.matrix.push()
                ctr = self.mass.center
                trn = multiply(bmat, mathutils.Vector((ctr[0], ctr[2], ctr[1])))
                gpu.matrix.translate(trn)
                draw_cross(0.05, color)
            finally:
                gpu.matrix.pop()
        else:
            bgl.glEnable(bgl.GL_BLEND)
            if bpy.context.active_bone \
                and (bpy.context.active_bone.id_data == obj_arm.data) \
                and (bpy.context.active_bone.name == bone.name):
                bgl.glColor4f(1.0, 0.0, 0.0, 0.7)
            else:
                bgl.glColor4f(0.0, 0.0, 1.0, 0.5)
            prev_line_width = bgl.Buffer(bgl.GL_FLOAT, [1])
            bgl.glGetFloatv(bgl.GL_LINE_WIDTH, prev_line_width)
            bgl.glPushMatrix()
            try:
                mat = multiply(
                    obj_arm.matrix_world,
                    obj_arm.pose.bones[bone.name].matrix,
                    mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
                )
                bmat = mat
                bgl.glLineWidth(2)
                mat = multiply(mat, shape.get_matrix_basis())
                bgl.glMultMatrixf(matrix_to_buffer(mat.transposed()))
                if shape.type == '1':  # box
                    draw_wire_cube(*shape.box_hsz)
                if shape.type == '2':  # sphere
                    draw_wire_sphere(shape.sph_rad, 16)
                if shape.type == '3':  # cylinder
                    draw_wire_cylinder(shape.cyl_rad, shape.cyl_hgh * 0.5, 16)
                bgl.glPopMatrix()
                bgl.glPushMatrix()
                ctr = self.mass.center
                trn = multiply(bmat, mathutils.Vector((ctr[0], ctr[2], ctr[1])))
                bgl.glTranslatef(*trn)
                draw_cross(0.05)
            finally:
                bgl.glPopMatrix()
                bgl.glLineWidth(prev_line_width[0])


prop_groups = (
    (ShapeProperties, shape_properties, False),
    (BreakProperties, break_properties, False),
    (IKJointProperties, ik_joint_properties, False),
    (MassProperties, mass_properties, False),
    (XRayBoneProperties, xray_bone_properties, True),
)


def register():
    for prop_group, props, is_group in prop_groups:
        assign_props([
            (props, prop_group),
        ])
        bpy.utils.register_class(prop_group)
        if is_group:
            prop_group.b_type.xray = bpy.props.PointerProperty(type=prop_group)


def unregister():
    for prop_group, props, is_group in reversed(prop_groups):
        if is_group:
            del prop_group.b_type.xray
        bpy.utils.unregister_class(prop_group)
