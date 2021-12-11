# standart modules
import math

# blender modules
import bpy
import mathutils

# addon modules
from .. import version_utils
from .. import text


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
}
bone_layers = [False, ] * 32
last_layer = bone_layers.copy()
last_layer[31] = True
layer_30 = bone_layers.copy()
layer_30[30] = True


def create_ik(bone, chain_length, pole_target_offset):
    bone_name = bone.name
    bone_root_name = bone.parent.name
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    obj = bpy.context.object
    arm = obj.data
    current_bone = arm.edit_bones[bone_name]
    ik_bones = {}
    fk_bones = {}
    # create ik/fk bones
    for chain_index in range(chain_length):
        current_bone.layers = last_layer
        # ik bone
        ik_bone = arm.edit_bones.new(current_bone.name + ' ik')
        ik_bones[current_bone.name] = ik_bone.name
        ik_bone.head = current_bone.head
        ik_bone.tail = current_bone.tail
        ik_bone.roll = current_bone.roll
        ik_bone.layers = layer_30
        # fk bone
        fk_bone = arm.edit_bones.new(current_bone.name + ' fk')
        fk_bones[current_bone.name] = fk_bone.name
        fk_bone.head = current_bone.head
        fk_bone.tail = current_bone.tail
        fk_bone.roll = current_bone.roll
        current_bone = current_bone.parent
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
    target_bone = arm.edit_bones.new(bone.name + ' ik target')
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
        child_transform_bone = arm.edit_bones.new(child_bone_name + ' transform')
        child_transform_bone.head = child_edit_bone.head
        child_transform_bone.tail = child_edit_bone.tail
        child_transform_bone.roll = child_edit_bone.roll
        child_transform_bone.parent = target_bone
        child_transform_bone.layers = last_layer
        subtarget_name = child_transform_bone.name
        bpy.ops.object.mode_set(mode='POSE', toggle=False)
        child_pose_bone = obj.pose.bones[child_bone_name]
        copy_rotation_constr = child_pose_bone.constraints.new('COPY_ROTATION')
        copy_rotation_constr.target = obj
        copy_rotation_constr.subtarget = subtarget_name
        copy_rotation_constr.enabled = True
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
    pole_name = bone_name + ' pole_target'
    pole_edit_bone = arm.edit_bones.new(pole_name)
    pole_edit_bone.head = final_vec
    pole_tail_offset = mathutils.Vector((0.0, 0.1, 0.0))
    pole_edit_bone.tail = final_vec + pole_tail_offset
    # Enter Pose Mode to set up data for pole angle
    bpy.ops.object.mode_set(mode='POSE', toggle=False)

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


class XRAY_OT_create_ik(bpy.types.Operator):
    bl_idname = 'io_scene_xray.create_ik'
    bl_label = 'Create IK'
    bl_options = {'REGISTER', 'UNDO'}

    if not version_utils.IS_28:
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
        split = version_utils.layout_split(self.layout, 0.35)
        split.label(text='Chain Length:')
        split.prop(self, 'chain_length', text='')

        split = version_utils.layout_split(self.layout, 0.35)
        split.label(text='Pole Target Offset:')
        split.prop(self, 'pole_target_offset', text='')

    def execute(self, context):
        if not len(context.selected_pose_bones):
            self.report({'WARNING'}, text.warn.ik_no_selected_bones)
            return {'FINISHED'}
        for bone in context.selected_pose_bones:
            create_ik(bone, self.chain_length, self.pole_target_offset)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def register():
    version_utils.assign_props([(props, XRAY_OT_create_ik), ])
    bpy.utils.register_class(XRAY_OT_create_ik)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_create_ik)
