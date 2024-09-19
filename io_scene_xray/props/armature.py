# standart modules
import functools

# blender modules
import bpy
import mathutils
import gpu

# addon modules
from .. import utils
from .. import viewport

if not utils.version.IS_34:
    import bgl


class XRayArmatureProps(bpy.types.PropertyGroup):
    b_type = bpy.types.Armature

    display_bone_shapes = bpy.props.BoolProperty(
        name='Display Bone Shapes',
        default=False
    )
    display_bone_mass_centers = bpy.props.BoolProperty(
        name='Display Bone Mass Centers',
        default=False
    )
    bone_mass_center_cross_size = bpy.props.FloatProperty(
        name='Сrosshair Size',
        default=0.02,
        min=0.00001,
        precision=5
    )
    joint_limits_type = bpy.props.EnumProperty(
        items=(
            ('IK', 'IK', ''),
            # Added a space to the beginning and end of
            # the string so that the translation does not work.
            ('XRAY', ' X-Ray ', '')
        ),
        name='Export Limits From',
        default='IK'
    )
    display_bone_limits = bpy.props.BoolProperty(
        name='Display Bone Limits',
        default=False
    )
    display_bone_limits_radius = bpy.props.FloatProperty(
        name='Gizmo Radius',
        default=0.1,
        min=0.00001,
        precision=5
    )
    display_bone_limit_x = bpy.props.BoolProperty(
        name='Limit X',
        default=True
    )
    display_bone_limit_y = bpy.props.BoolProperty(
        name='Limit Y',
        default=True
    )
    display_bone_limit_z = bpy.props.BoolProperty(
        name='Limit Z',
        default=True
    )

    def check_different_version_bones(self):
        return functools.reduce(
            lambda x, y: x | y,
            [
                bone.xray.shape.check_version_different()
                for bone in self.id_data.bones
            ],
            0,
        )

    def initialize(self, operation, addon_ver):
        if operation == 'LOADED':
            for bone in self.id_data.bones:
                if bone.xray.version < addon_ver:
                    data = bone.xray
                    data.version = addon_ver
                    ik = data.ikjoint
                    ik.slide_min = ik.lim_x_min
                    ik.slide_max = ik.lim_x_max

        elif operation == 'CREATED':
            for bone in self.id_data.bones:
                bone.xray.version = addon_ver

    def _gen_shape(self, obj, bone, ctx):
        shape = bone.xray.shape
        mat = self.mul(
            obj.matrix_world,
            obj.pose.bones[bone.name].matrix,
            mathutils.Matrix.Scale(-1, 4, (0, 0, 1)),
            shape.get_matrix()
        )

        coords = ctx.geom['shape'][self.state]['coords']
        lines = ctx.geom['shape'][self.state]['lines']
        faces = ctx.geom['shape'][self.state]['faces']

        # box
        if shape.type == '1':
            viewport.geom.gen_cube_geom(mat, coords, lines, faces)

        # sphere
        elif shape.type == '2':
            viewport.geom.gen_sphere_geom(mat, coords, lines, faces)

        # cylinder
        elif shape.type == '3':
            viewport.geom.gen_cylinder_geom(mat, coords, lines, faces)

    def _gen_center(self, obj, bone, ctx):
        mat = self.mul(
            obj.matrix_world,
            obj.pose.bones[bone.name].matrix,
            mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
        )
        ctr = bone.xray.mass.center
        trn = mathutils.Matrix.Translation(self.mul(
            mat,
            mathutils.Vector((ctr[0], ctr[2], ctr[1]))
        ))
        cross_size = obj.data.xray.bone_mass_center_cross_size

        coords = ctx.geom['mass'][self.state]['coords']
        lines = ctx.geom['mass'][self.state]['lines']

        viewport.geom.gen_cross_geom(cross_size, trn, coords, lines)

    def _get_geom_state(self, obj, bone, ctx):
        if self.is_pose:
            active = bpy.context.active_bone
            if active and active.id_data == obj.data and active.name == bone.name:
                self.state = 'active'
            elif bone.select:
                self.state = 'sel'
            else:
                self.state = 'desel'
        else:
            self.state = 'obj'

    def _gen_geometry(self, obj, ctx):
        for bone in obj.data.bones:

            # check bone visibility
            exportable = bone.xray.exportable
            hided = bone.hide or not exportable
            if hided:
                continue

            # get geometry state
            self._get_geom_state(obj, bone, ctx)

            # None and Custom types don't have shape
            shape = bone.xray.shape
            if shape.type in ('0', '4'):
                continue

            draw_overlays = not hided and self.is_pose

            # generate shape
            if self.shapes:
                self._gen_shape(obj, bone, ctx)

            # generate mass center
            if self.centers:
                self._gen_center(obj, bone, ctx)

            # draw limits
            if self.limits and draw_overlays:
                self._draw_limits(obj, bone, ctx)

    def _check_arm_vis(self, obj):
        visible = True

        if utils.version.IS_28:
            if not obj.name in bpy.context.view_layer.objects:
                visible = False

        else:
            if not obj.name in bpy.context.scene.objects:
                visible = False
            visible_armature_object = False
            for layer_index, layer in enumerate(obj.layers):
                scene_layer = bpy.context.scene.layers[layer_index]
                if scene_layer and layer:
                    visible_armature_object = True
                    break
            if not visible_armature_object:
                visible = False

        return visible

    def _draw_limits(self, obj, bone, ctx):
        active_obj = bpy.context.active_object
        if active_obj:
            is_active = active_obj.name == obj.name
        else:
            is_active = False

        has_limits = bone.xray.ikjoint.type in {'2', '3', '5'}
        if is_active and has_limits and bone.select:

            arm_xray = obj.data.xray

            if utils.version.IS_28:
                gpu.matrix.push()
            else:
                bgl.glPushMatrix()

            translate = obj.pose.bones[bone.name].matrix.to_translation()
            mat_translate = mathutils.Matrix.Translation(translate)
            mat_rotate = obj.data.bones[bone.name].matrix_local.to_euler().to_matrix().to_4x4()
            if bone.parent:
                mat_rotate_parent = obj.pose.bones[bone.parent.name].matrix_basis.to_euler().to_matrix().to_4x4()
            else:
                mat_rotate_parent = mathutils.Matrix()

            mat = self.mul(
                obj.matrix_world,
                mat_translate,
                self.mul(mat_rotate, mat_rotate_parent),
                mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
            )
            if utils.version.IS_28:
                gpu.matrix.multiply_matrix(mat)
            else:
                bgl.glMultMatrixf(viewport.gl_utils.matrix_to_buffer(mat.transposed()))

            pose_bone = obj.pose.bones[bone.name]
            if pose_bone.rotation_mode == 'QUATERNION':
                rotate = pose_bone.rotation_quaternion.to_euler('ZXY')
            else:
                rotate = pose_bone.rotation_euler.to_matrix().to_euler('ZXY')

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

            draw_limits = viewport.get_draw_joint_limits()

            if arm_xray.display_bone_limit_x and (is_joint or is_wheel):
                draw_limits(
                    rotate.x,
                    limits[0],
                    limits[1],
                    'X',
                    arm_xray.display_bone_limits_radius
                )

            if arm_xray.display_bone_limit_y and is_joint:
                draw_limits(
                    rotate.y,
                    limits[2],
                    limits[3],
                    'Y',
                    arm_xray.display_bone_limits_radius
                )

            if arm_xray.display_bone_limit_z and is_joint:
                draw_limits(
                    rotate.z,
                    limits[4],
                    limits[5],
                    'Z',
                    arm_xray.display_bone_limits_radius
                )

            # slider limits
            if arm_xray.display_bone_limit_z and is_slider:
                draw_slider_rotation_limits = viewport.get_draw_slider_rotation_limits()
                draw_slider_rotation_limits(
                    rotate.z,
                    limits[2],
                    limits[3],
                    arm_xray.display_bone_limits_radius
                )
                bone_matrix = obj.data.bones[bone.name].matrix_local.to_4x4()
                slider_mat = self.mul(
                    obj.matrix_world,
                    bone_matrix
                )
                if utils.version.IS_28:
                    gpu.matrix.pop()
                    gpu.matrix.push()
                    gpu.matrix.multiply_matrix(slider_mat)
                else:
                    bgl.glPopMatrix()
                    bgl.glPushMatrix()
                    bgl.glMultMatrixf(viewport.gl_utils.matrix_to_buffer(slider_mat.transposed()))
                draw_slider_slide_limits = viewport.get_draw_slider_slide_limits()
                draw_slider_slide_limits(ik.slide_min, ik.slide_max, color)

            if utils.version.IS_28:
                gpu.matrix.pop()
            else:
                bgl.glPopMatrix()

    def ondraw_postview(self, obj, ctx):

        # get armature state
        hide_arm_obj = not utils.version.get_object_visibility(obj)
        self.is_pose = obj.mode == 'POSE'
        self.is_edit = obj.mode == 'EDIT'

        if hide_arm_obj:
            return

        if self.is_edit:
            return

        # check armature visibility
        arm_visible = self._check_arm_vis(obj)
        if not arm_visible:
            return

        arm_data = obj.data.xray
        self.mul = utils.version.get_multiply()

        # what to display
        self.shapes = arm_data.display_bone_shapes
        self.centers = arm_data.display_bone_mass_centers
        self.limits = arm_data.display_bone_limits

        # generate geometry
        self._gen_geometry(obj, ctx)


def register():
    utils.version.register_classes(XRayArmatureProps)


def unregister():
    utils.version.unregister_prop_groups(XRayArmatureProps)
