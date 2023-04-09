# standart modules
import math

# blender modules
import bpy
import mathutils
import bgl
import gpu

# addon modules
from . import utility
from .. import viewport
from .. import ops
from .. import utils


shape_properties = {
    'type': bpy.props.EnumProperty(
        items=(
            ('0', 'None', ''),
            ('1', 'Box', ''),
            ('2', 'Sphere', ''),
            ('3', 'Cylinder', '')
        ),
        update=lambda self, ctx: ops.edit_helpers.bone_shape.HELPER.update(),
    ),
    'flags': bpy.props.IntProperty(),
    'flags_nopickable': utility.gen_flag_prop(mask=0x1),
    'flags_removeafterbreak': utility.gen_flag_prop(mask=0x2),
    'flags_nophysics': utility.gen_flag_prop(mask=0x4),
    'flags_nofogcollider': utility.gen_flag_prop(mask=0x8),
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

    if not utils.version.IS_28:
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
            return utils.version.multiply(
                mathutils.Matrix.Translation(self.box_trn),
                mathutils.Matrix((rot[0:3], rot[3:6], rot[6:9])).transposed().to_4x4()
            )
        if typ == '2':  # sphere
            return mathutils.Matrix.Translation(self.sph_pos)
        if typ == '3':  # cylinder
            v_dir = mathutils.Vector(self.cyl_dir)
            q_rot = v_dir.rotation_difference((0, 1, 0))
            return utils.version.multiply(
                mathutils.Matrix.Translation(self.cyl_pos),
                q_rot.to_matrix().transposed().to_4x4()
            )


break_properties = {
    'force': bpy.props.FloatProperty(min=0.0),
    'torque': bpy.props.FloatProperty(min=0.0)
}


class BreakProperties(bpy.types.PropertyGroup):
    if not utils.version.IS_28:
        for prop_name, prop_value in break_properties.items():
            exec('{0} = break_properties.get("{0}")'.format(prop_name))


ik_joint_properties = {
    'type': bpy.props.EnumProperty(items=(
        ('4', 'None', ''),
        ('0', 'Rigid', ''),
        ('1', 'Cloth', ''),
        ('2', 'Joint', ''),
        ('3', 'Wheel', ''),
        ('5', 'Slider', ''))
    ),
    'lim_x_min': bpy.props.FloatProperty(
        min=-math.pi, max=math.pi,
        update=ops.joint_limits.update_limit,
        subtype='ANGLE'
    ),
    'lim_x_max': bpy.props.FloatProperty(
        min=-math.pi, max=math.pi,
        update=ops.joint_limits.update_limit,
        subtype='ANGLE'
    ),
    'lim_x_spr': bpy.props.FloatProperty(min=0.0, max=1000.0),
    'lim_x_dmp': bpy.props.FloatProperty(min=0.0, max=1000.0),
    'lim_y_min': bpy.props.FloatProperty(
        min=-math.pi, max=math.pi,
        update=ops.joint_limits.update_limit,
        subtype='ANGLE'
    ),
    'lim_y_max': bpy.props.FloatProperty(
        min=-math.pi, max=math.pi,
        update=ops.joint_limits.update_limit,
        subtype='ANGLE'
    ),
    'lim_y_spr': bpy.props.FloatProperty(min=0.0, max=1000.0),
    'lim_y_dmp': bpy.props.FloatProperty(min=0.0, max=1000.0),
    'lim_z_min': bpy.props.FloatProperty(
        min=-math.pi, max=math.pi,
        update=ops.joint_limits.update_limit,
        subtype='ANGLE'
    ),
    'lim_z_max': bpy.props.FloatProperty(
        min=-math.pi, max=math.pi,
        update=ops.joint_limits.update_limit,
        subtype='ANGLE'
    ),
    'lim_z_spr': bpy.props.FloatProperty(min=0.0, max=1000.0),
    'lim_z_dmp': bpy.props.FloatProperty(min=0.0, max=1000.0),
    'spring': bpy.props.FloatProperty(min=0.0, max=1000.0),
    'damping': bpy.props.FloatProperty(min=0.0, max=1000.0),
    'is_rigid': bpy.props.BoolProperty(get=lambda self: self.type == '0')
}


class IKJointProperties(bpy.types.PropertyGroup):
    if not utils.version.IS_28:
        for prop_name, prop_value in ik_joint_properties.items():
            exec('{0} = ik_joint_properties.get("{0}")'.format(prop_name))


mass_properties = {
    'value': bpy.props.FloatProperty(name='Mass', precision=3, min=0.0),
    'center': bpy.props.FloatVectorProperty(name='Center of Mass', precision=3)
}


class MassProperties(bpy.types.PropertyGroup):
    if not utils.version.IS_28:
        for prop_name, prop_value in mass_properties.items():
            exec('{0} = mass_properties.get("{0}")'.format(prop_name))


def set_ikflags_breakable(self, value):
    self.ikflags = self.ikflags | 0x1 if value else self.ikflags & ~0x1


xray_bone_properties = {
    'exportable': bpy.props.BoolProperty(
        name='Exportable',
        default=True,
        description='Enable Bone to be exported'
    ),
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
    'friction': bpy.props.FloatProperty(min=0.0),
    'mass': bpy.props.PointerProperty(type=MassProperties)
}


class XRayBoneProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Bone

    if not utils.version.IS_28:
        for prop_name, prop_value in xray_bone_properties.items():
            exec('{0} = xray_bone_properties.get("{0}")'.format(prop_name))

    def ondraw_postview(self, obj_arm, bone):
        # draw limits
        arm_xray = obj_arm.data.xray
        if utils.version.IS_28:
            hide_global = obj_arm.hide_viewport
            view_layer = bpy.context.view_layer
            hide_viewport = obj_arm.hide_get(view_layer=view_layer)
            hide = hide_global or hide_viewport
        else:
            hide = obj_arm.hide
        multiply = utils.version.get_multiply()

        prev_line_width = bgl.Buffer(bgl.GL_FLOAT, [1])
        bgl.glGetFloatv(bgl.GL_LINE_WIDTH, prev_line_width)
        bgl.glLineWidth(viewport.const.LINE_WIDTH)

        bgl.glEnable(bgl.GL_BLEND)

        hide_bone = bone.hide
        hided = hide or hide_bone
        is_pose = obj_arm.mode == 'POSE'
        exportable = bone.xray.exportable
        draw_overlays = not hided and is_pose and exportable

        preferences = utils.version.get_preferences()
        # set color
        if is_pose:
            active_bone = bpy.context.active_bone
            color = None
            if active_bone:
                if active_bone.id_data == obj_arm.data:
                    if active_bone.name == bone.name:
                        color = preferences.gl_active_shape_color
            if color is None:
                if bone.select:
                    color = preferences.gl_select_shape_color
                else:
                    color = preferences.gl_shape_color
        else:
            color = preferences.gl_object_mode_shape_color

        if draw_overlays and arm_xray.display_bone_limits:
            context_obj = bpy.context.active_object
            if context_obj:
                is_active_object = context_obj.name == obj_arm.name
            else:
                is_active_object = False
            has_limits = bone.xray.ikjoint.type in {'2', '3', '5'}
            if bone.select and has_limits and is_active_object:
                draw_joint_limits = viewport.get_draw_joint_limits()

                if utils.version.IS_28:
                    gpu.matrix.push()
                else:
                    bgl.glPushMatrix()

                translate = obj_arm.pose.bones[bone.name].matrix.to_translation()
                mat_translate = mathutils.Matrix.Translation(translate)
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
                if utils.version.IS_28:
                    gpu.matrix.multiply_matrix(mat)
                else:
                    bgl.glMultMatrixf(
                        viewport.gl_utils.matrix_to_buffer(mat.transposed())
                    )

                pose_bone = obj_arm.pose.bones[bone.name]
                if pose_bone.rotation_mode == 'QUATERNION':
                    rotate = pose_bone.rotation_quaternion.to_euler('XYZ')
                else:
                    rotate = obj_arm.pose.bones[bone.name].rotation_euler

                if arm_xray.joint_limits_type == 'IK':
                    limits = (
                        pose_bone.ik_min_x, pose_bone.ik_max_x,
                        pose_bone.ik_min_y, pose_bone.ik_max_y,
                        pose_bone.ik_min_z, pose_bone.ik_max_z
                    )
                else:
                    ik = bone.xray.ikjoint
                    limits = (
                        ik.lim_x_min, ik.lim_x_max,
                        ik.lim_y_min, ik.lim_y_max,
                        ik.lim_z_min, ik.lim_z_max
                    )

                is_joint = bone.xray.ikjoint.type == '2'
                is_wheel = bone.xray.ikjoint.type == '3'
                is_slider = bone.xray.ikjoint.type == '5'

                if arm_xray.display_bone_limit_x and (is_joint or is_wheel):
                    draw_joint_limits(
                        rotate.x, limits[0], limits[1], 'X',
                        arm_xray.display_bone_limits_radius
                    )

                if arm_xray.display_bone_limit_y and is_joint:
                    draw_joint_limits(
                        rotate.y, limits[2], limits[3], 'Y',
                        arm_xray.display_bone_limits_radius
                    )

                if arm_xray.display_bone_limit_z and is_joint:
                    draw_joint_limits(
                        rotate.z, limits[4], limits[5], 'Z',
                        arm_xray.display_bone_limits_radius
                    )

                # slider limits
                if arm_xray.display_bone_limit_z and is_slider:
                    draw_slider_rotation_limits = viewport.get_draw_slider_rotation_limits()
                    draw_slider_rotation_limits(
                        rotate.z, limits[2], limits[3],
                        arm_xray.display_bone_limits_radius
                    )
                    bone_matrix = obj_arm.data.bones[bone.name].matrix_local.to_4x4()
                    slider_mat = multiply(
                        obj_arm.matrix_world,
                        bone_matrix
                    )
                    if utils.version.IS_28:
                        gpu.matrix.pop()
                        gpu.matrix.push()
                        gpu.matrix.multiply_matrix(slider_mat)
                    else:
                        bgl.glPopMatrix()
                        bgl.glPushMatrix()
                        bgl.glMultMatrixf(
                            viewport.gl_utils.matrix_to_buffer(slider_mat.transposed())
                        )
                    draw_slider_slide_limits = viewport.get_draw_slider_slide_limits()
                    draw_slider_slide_limits(limits[0], limits[1], color)

                if utils.version.IS_28:
                    gpu.matrix.pop()
                else:
                    bgl.glPopMatrix()

        mat = multiply(
            obj_arm.matrix_world,
            obj_arm.pose.bones[bone.name].matrix,
            mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
        )
        bmat = mat

        if not utils.version.IS_28:
            bgl.glColor4f(*color)

        shape = self.shape
        if shape.type == '0':
            bgl.glLineWidth(prev_line_width[0])
            return

        # draw mass centers
        is_edit = obj_arm.mode == 'EDIT'
        draw_mass = obj_arm.data.xray.display_bone_mass_centers
        if draw_mass and exportable and not hided and not is_edit:
            ctr = self.mass.center
            trn = multiply(
                bmat,
                mathutils.Vector((ctr[0], ctr[2], ctr[1]))
            )
            cross_size = obj_arm.data.xray.bone_mass_center_cross_size
            if utils.version.IS_28:
                gpu.matrix.push()
                gpu.matrix.translate(trn)
                viewport.draw_cross(cross_size, color=color)
                gpu.matrix.pop()
            else:
                bgl.glPopMatrix()
                bgl.glPushMatrix()
                bgl.glTranslatef(*trn)
                viewport.draw_cross(cross_size)
                bgl.glPopMatrix()

        # draw shapes
        draw_shapes = obj_arm.data.xray.display_bone_shapes
        if hided or not draw_shapes or not exportable or is_edit:
            bgl.glLineWidth(prev_line_width[0])
            return

        if utils.version.IS_28:
            if not obj_arm.name in bpy.context.view_layer.objects:
                bgl.glLineWidth(prev_line_width[0])
                return
        else:
            if not obj_arm.name in bpy.context.scene.objects:
                bgl.glLineWidth(prev_line_width[0])
                return
            visible_armature_object = False
            for layer_index, layer in enumerate(obj_arm.layers):
                scene_layer = bpy.context.scene.layers[layer_index]
                if scene_layer and layer:
                    visible_armature_object = True
                    break

            if not visible_armature_object:
                bgl.glLineWidth(prev_line_width[0])
                return

        if utils.version.IS_28:
            gpu.matrix.push()
            try:
                mat = multiply(mat, shape.get_matrix_basis())
                gpu.matrix.multiply_matrix(mat)
                if shape.type == '1':  # box
                    viewport.draw_cube(*shape.box_hsz, color=color)
                if shape.type == '2':  # sphere
                    viewport.draw_sphere(
                        shape.sph_rad,
                        viewport.const.BONE_SHAPE_SPHERE_SEGMENTS_COUNT,
                        color=color
                    )
                if shape.type == '3':  # cylinder
                    viewport.draw_cylinder(
                        shape.cyl_rad,
                        shape.cyl_hgh * 0.5,
                        viewport.const.BONE_SHAPE_CYLINDER_SEGMENTS_COUNT,
                        color
                    )
            finally:
                gpu.matrix.pop()
        else:
            bgl.glPopMatrix()
            bgl.glPushMatrix()
            try:
                mat = multiply(mat, shape.get_matrix_basis())
                bgl.glMultMatrixf(
                    viewport.gl_utils.matrix_to_buffer(mat.transposed())
                )
                if shape.type == '1':  # box
                    viewport.draw_cube(*shape.box_hsz)
                if shape.type == '2':  # sphere
                    viewport.draw_sphere(
                        shape.sph_rad,
                        viewport.const.BONE_SHAPE_SPHERE_SEGMENTS_COUNT
                    )
                if shape.type == '3':  # cylinder
                    viewport.draw_cylinder(
                        shape.cyl_rad,
                        shape.cyl_hgh * 0.5,
                        viewport.const.BONE_SHAPE_CYLINDER_SEGMENTS_COUNT
                    )
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
        utils.version.assign_props([
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
