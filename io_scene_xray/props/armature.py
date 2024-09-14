# standart modules
import functools

# blender modules
import bpy
import mathutils

# addon modules
from .. import utils
from .. import viewport


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

    def _gen_shapes(self, obj, ctx):
        for bone in obj.data.bones:

            # check bone visibility
            exportable = bone.xray.exportable
            hided = bone.hide or not exportable
            if hided:
                continue

            # None and Custom types don't have shape
            shape = bone.xray.shape
            if shape.type in ('0', '4'):
                continue

            mat = self.mul(
                obj.matrix_world,
                obj.pose.bones[bone.name].matrix,
                mathutils.Matrix.Scale(-1, 4, (0, 0, 1)),
                shape.get_matrix_basis()
            )

            # box
            if shape.type == '1':
                viewport.geom.gen_cube_geom(mat, ctx.coords, ctx.lines, ctx.faces)

            # sphere
            elif shape.type == '2':
                viewport.geom.gen_sphere_geom(mat, ctx.coords, ctx.lines, ctx.faces)

            # cylinder
            elif shape.type == '3':
                viewport.geom.gen_cylinder_geom(mat, ctx.coords, ctx.lines, ctx.faces)

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

    def ondraw_postview(self, obj, ctx):

        # get armature state
        hide_arm_obj = not utils.version.get_object_visibility(obj)
        is_pose = obj.mode == 'POSE'
        is_edit = obj.mode == 'EDIT'

        if hide_arm_obj:
            return

        if is_edit:
            return

        # check armature visibility
        arm_visible = self._check_arm_vis(obj)
        if not arm_visible:
            return

        arm_data = obj.data.xray
        self.mul = utils.version.get_multiply()

        # what to display
        shapes = arm_data.display_bone_shapes
        centers = arm_data.display_bone_mass_centers
        limits = arm_data.display_bone_limits

        # generate shapes geometry
        if shapes:
            self._gen_shapes(obj, ctx)


def register():
    utils.version.register_classes(XRayArmatureProps)


def unregister():
    utils.version.unregister_prop_groups(XRayArmatureProps)
