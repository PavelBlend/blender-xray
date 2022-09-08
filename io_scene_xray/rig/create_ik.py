# standart modules
import math

# blender modules
import bpy
import mathutils

# addon modules
from .. import utils
from .. import text


bone_layers = [False, ] * 32
last_layer = bone_layers.copy()
last_layer[31] = True
layer_30 = bone_layers.copy()
layer_30[30] = True
IK_FK_PROP_NAME = 'ik_fk'
ik_suffix = ' ik'
fk_suffix = ' fk'
ik_target_suffix = ' ik_target'
ik_pole_target_suffix = ' ik_pole_target'
bone_suffix_list = (
    ik_suffix,
    fk_suffix,
    ik_target_suffix,
    ik_pole_target_suffix
)


def create_ik(bone, chain_length, pole_target_offset, category_name):
    bone_name = bone.name
    bone_root_name = bone.parent.name
    if not bone.parent:
        return
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    obj = bpy.context.object
    arm = obj.data
    current_bone = arm.edit_bones[bone_name]
    ik_bones = {}
    fk_bones = {}
    fk_last_bone_name = None
    # create ik/fk bones
    for chain_index in range(chain_length):
        current_bone.layers = last_layer
        # ik bone
        ik_bone = arm.edit_bones.new(current_bone.name + ik_suffix)
        ik_bones[current_bone.name] = ik_bone.name
        ik_bone.head = current_bone.head
        ik_bone.tail = current_bone.tail
        ik_bone.roll = current_bone.roll
        ik_bone.layers = layer_30
        # fk bone
        fk_bone = arm.edit_bones.new(current_bone.name + fk_suffix)
        fk_bones[current_bone.name] = fk_bone.name
        fk_bone.head = current_bone.head
        fk_bone.tail = current_bone.tail
        fk_bone.roll = current_bone.roll
        current_bone = current_bone.parent
        if not chain_index:
            fk_last_bone_name = fk_bone.name
    # set parent for ik/fk bones
    for edit_bone in arm.edit_bones:
        ik_bone_name = ik_bones.get(edit_bone.name, None)
        fk_bone_name = fk_bones.get(edit_bone.name, None)
        parent = edit_bone.parent
        if ik_bone_name:
            ik_bone = arm.edit_bones[ik_bone_name]
            ik_parent_name = ik_bones.get(parent.name, None)
            if ik_parent_name:
                ik_parent = arm.edit_bones[ik_parent_name]
                ik_bone.parent = ik_parent
            else:
                ik_bone.parent = parent
        if fk_bone_name:
            fk_bone = arm.edit_bones[fk_bone_name]
            fk_parent_name = fk_bones.get(parent.name, None)
            if fk_parent_name:
                fk_parent = arm.edit_bones[fk_parent_name]
                fk_bone.parent = fk_parent
            else:
                fk_bone.parent = parent
    target_bone = arm.edit_bones.new(bone.name + ik_target_suffix)
    target_bone_name = target_bone.name
    target_bone.head = bone.tail
    tail = target_bone.head.copy()
    tail[2] += bone.length / 4
    target_bone.tail = tail
    children = []
    for child in bone.children:
        if bone.name.startswith(child.name):
            continue
        children.append(child)
    # create transform bone
    if len(children) == 1:
        child_bone = children[0]
        child_bone_name = child_bone.name
        child_edit_bone = arm.edit_bones[child_bone_name]
        child_edit_bone.layers = last_layer
        # create ik bone
        child_ik_bone = arm.edit_bones.new(child_bone_name + ik_suffix)
        child_ik_bone.head = child_edit_bone.head
        child_ik_bone.tail = child_edit_bone.tail
        child_ik_bone.roll = child_edit_bone.roll
        child_ik_bone.parent = target_bone
        child_ik_bone.layers = last_layer
        ik_subtarget_name = child_ik_bone.name
        # create fk bone
        child_fk_bone = arm.edit_bones.new(child_bone_name + fk_suffix)
        child_fk_bone.head = child_edit_bone.head
        child_fk_bone.tail = child_edit_bone.tail
        child_fk_bone.roll = child_edit_bone.roll
        child_fk_bone.parent = arm.edit_bones[fk_last_bone_name]
        fk_subtarget_name = child_fk_bone.name
        # create constraints
        bpy.ops.object.mode_set(mode='POSE', toggle=False)
        child_pose_bone = obj.pose.bones[child_bone_name]
        # ik
        copy_rotation_constr = child_pose_bone.constraints.new('COPY_ROTATION')
        copy_rotation_constr.name = 'ik'
        copy_rotation_constr.target = obj
        copy_rotation_constr.subtarget = ik_subtarget_name
        if utils.version.IS_28:
            copy_rotation_constr.enabled = True
        # fk
        copy_transforms_constr = child_pose_bone.constraints.new('COPY_TRANSFORMS')
        copy_transforms_constr.name = 'fk'
        copy_transforms_constr.target = obj
        copy_transforms_constr.subtarget = fk_subtarget_name
        if utils.version.IS_28:
            copy_transforms_constr.enabled = True
        # create ik drivers
        ik_driver = copy_rotation_constr.driver_add('influence').driver
        ik_driver.expression = IK_FK_PROP_NAME
        var = ik_driver.variables.new()
        var.name = IK_FK_PROP_NAME
        var.type = 'SINGLE_PROP'
        target = var.targets[0]
        target.id_type = 'OBJECT'
        target.id = obj
        target.data_path = 'pose.bones["{0}"]["{1}"]'.format(
            target_bone_name,
            IK_FK_PROP_NAME
        )
        # create fk drivers
        fk_driver = copy_transforms_constr.driver_add('influence').driver
        fk_driver.expression = '1.0 - {}'.format(IK_FK_PROP_NAME)
        var = fk_driver.variables.new()
        var.name = IK_FK_PROP_NAME
        var.type = 'SINGLE_PROP'
        target = var.targets[0]
        target.id_type = 'OBJECT'
        target.id = obj
        target.data_path = 'pose.bones["{0}"]["{1}"]'.format(
            target_bone_name,
            IK_FK_PROP_NAME
        )

    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    bpy.ops.armature.select_all(action='DESELECT')

    ########################################
    # Create and place IK pole target bone #
    #          by Marco Giordano           #
    ########################################

    # https://blender.stackexchange.com/questions/97606

    arm_edit_bones = arm.edit_bones
    root_bone = arm_edit_bones[bone_name]
    for chain_index in range(chain_length - 1):
        root_bone = root_bone.parent
    bone_root_name = root_bone.name
    # Get points to define the plane on which to put the pole target
    A = arm_edit_bones[bone_root_name].head
    B = arm_edit_bones[bone_name].head
    C = arm_edit_bones[bone_name].tail
    # Vector of chain root to chain tip (wrist)
    AC = C - A
    # Vector of chain root to second bone's head
    AB = B - A
    # Multiply the two vectors to get the dot product
    dot_prod = AB * AC
    # Find the point on the vector AC projected from point B
    proj = dot_prod / AC.length
    # Normalize AC vector to keep it a reasonable magnitude
    start_end_norm = AC.normalized()
    # Project an arrow from AC projection point to point B
    proj_vec  = start_end_norm * proj
    arrow_vec = AB - proj_vec
    arrow_vec.normalize()
    # Place pole target at a reasonable distance from the chain
    arrow_vec *= pole_target_offset
    final_vec = arrow_vec + B
    # Add pole target bone and place it in the scene pointed to Z+
    pole_name = bone_name + ik_pole_target_suffix
    pole_edit_bone = arm.edit_bones.new(pole_name)
    pole_edit_bone.head = final_vec
    pole_tail_offset = mathutils.Vector((0.0, 0.1, 0.0))
    pole_edit_bone.tail = final_vec + pole_tail_offset
    # Enter Pose Mode to set up data for pole angle
    bpy.ops.object.mode_set(mode='POSE', toggle=False)
    # create ik/fk constraints
    current_bone = obj.pose.bones[bone_name]
    ik_fk_bones = []
    for chain_index in range(chain_length):
        ik_fk_bones.append(current_bone.name)
        # ik bone
        ik_bone_name = ik_bones[current_bone.name]
        ik_bone = obj.pose.bones[ik_bone_name]
        copy_transforms = current_bone.constraints.new('COPY_TRANSFORMS')
        copy_transforms.name = 'ik'
        copy_transforms.target = obj
        copy_transforms.subtarget = ik_bone.name
        # fk bone
        fk_bone_name = fk_bones[current_bone.name]
        fk_bone = obj.pose.bones[fk_bone_name]
        copy_transforms = current_bone.constraints.new('COPY_TRANSFORMS')
        copy_transforms.name = 'fk'
        copy_transforms.target = obj
        copy_transforms.subtarget = fk_bone.name
        # change current bone
        current_bone = current_bone.parent

    ##############
    # Pole Angle #
    # by Jerryno #
    ##############

    def signed_angle(vector_u, vector_v, normal):
        # Normal specifies orientation
        angle = vector_u.angle(vector_v)
        if vector_u.cross(vector_v).angle(normal) < 1:
            angle = -angle
        return angle

    def get_pole_angle(base_bone, ik_bone, pole_location):
        pole_normal = (ik_bone.tail - base_bone.head).cross(pole_location - base_bone.head)
        projected_pole_axis = pole_normal.cross(base_bone.tail - base_bone.head)
        return signed_angle(base_bone.x_axis, projected_pole_axis, base_bone.tail - base_bone.head)

    base_bone = obj.pose.bones[bone_root_name]
    ik_bone = obj.pose.bones[bone_name]
    pole_bone = obj.pose.bones[pole_name]
    pole_angle_in_radians = get_pole_angle(
        base_bone,
        ik_bone,
        pole_bone.matrix.translation
    )
    ik_constr_bone = obj.pose.bones[ik_bones[bone_name]]
    ik_constr = ik_constr_bone.constraints.new('IK')
    ik_constr.target = obj
    ik_constr.subtarget = target_bone_name
    ik_constr.pole_target = obj
    ik_constr.pole_subtarget = pole_name
    ik_constr.pole_angle = pole_angle_in_radians
    ik_constr.chain_count = chain_length
    # add drivers
    obj.pose.bones[target_bone_name][IK_FK_PROP_NAME] = 1.0
    obj.pose.bones[target_bone_name]['bone_category'] = category_name
    if utils.version.IS_28:
        ui_prop = obj.pose.bones[target_bone_name].id_properties_ui(IK_FK_PROP_NAME)
        ui_prop.update(
            min=0,
            max=1,
            soft_min=0,
            soft_max=1
        )
    for ik_fk_bone_name in ik_fk_bones:
        ik_fk_bone = obj.pose.bones[ik_fk_bone_name]
        # ik driver
        ik_constraint = ik_fk_bone.constraints['ik']
        ik_driver = ik_constraint.driver_add('influence').driver
        ik_driver.expression = IK_FK_PROP_NAME
        var = ik_driver.variables.new()
        var.name = IK_FK_PROP_NAME
        var.type = 'SINGLE_PROP'
        target = var.targets[0]
        target.id_type = 'OBJECT'
        target.id = obj
        target.data_path = 'pose.bones["{0}"]["{1}"]'.format(
            target_bone_name,
            IK_FK_PROP_NAME
        )
        # fk driver
        fk_constraint = ik_fk_bone.constraints['fk']
        fk_driver = fk_constraint.driver_add('influence').driver
        fk_driver.expression = '1.0 - {}'.format(IK_FK_PROP_NAME)
        var = fk_driver.variables.new()
        var.name = IK_FK_PROP_NAME
        var.type = 'SINGLE_PROP'
        target = var.targets[0]
        target.id_type = 'OBJECT'
        target.id = obj
        target.data_path = 'pose.bones["{0}"]["{1}"]'.format(
            target_bone_name,
            IK_FK_PROP_NAME
        )


props = {
    'chain_length': bpy.props.IntProperty(
        name='Chain Length',
        min=0,
        max=255,
        default=2
    ),
    'pole_target_offset': bpy.props.FloatProperty(
        name='Pole Target Offset',
        min=0.001,
        default=0.5
    ),
    'ik_fk_name': bpy.props.StringProperty(
        name='IK/FK Name',
        default='IK/FK Name'
    ),
}


class XRAY_OT_create_ik(bpy.types.Operator):
    bl_idname = 'io_scene_xray.create_ik'
    bl_label = 'Create IK'
    bl_options = {'REGISTER', 'UNDO'}

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        if context.object.type != 'ARMATURE':
            return False
        if context.mode != 'POSE':
            return False
        return True

    def draw(self, context):
        split = utils.version.layout_split(self.layout, 0.35)
        split.label(text='Chain Length:')
        split.prop(self, 'chain_length', text='')

        split = utils.version.layout_split(self.layout, 0.35)
        split.label(text='Pole Target Offset:')
        split.prop(self, 'pole_target_offset', text='')

        split = utils.version.layout_split(self.layout, 0.35)
        split.label(text='IK/FK Name:')
        split.prop(self, 'ik_fk_name', text='')

    @utils.set_cursor_state
    def execute(self, context):
        if not len(context.selected_pose_bones):
            self.report({'WARNING'}, text.warn.ik_no_selected_bones)
            return {'FINISHED'}
        for bone in context.selected_pose_bones:
            create_ik(
                bone,
                self.chain_length,
                self.pole_target_offset,
                self.ik_fk_name
            )
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def register():
    utils.version.assign_props([(props, XRAY_OT_create_ik), ])
    bpy.utils.register_class(XRAY_OT_create_ik)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_create_ik)
