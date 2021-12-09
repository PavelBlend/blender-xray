# standart modules
import math

# blender modules
import bpy

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
}


def create_ik(bone, chain_length):
    ik_constr = bone.constraints.new('IK')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='EDIT')
    obj = bpy.context.object
    arm = obj.data
    target_bone = arm.edit_bones.new(bone.name + ' ik target')
    target_bone.head = bone.tail
    tail = target_bone.head.copy()
    tail[2] += bone.length / 4
    target_bone.tail = tail
    ik_constr.target = obj
    ik_constr.subtarget = target_bone.name
    children = []
    for child in bone.children:
        if bone.name.startswith(child.name):
            continue
        children.append(child)
    if len(children) == 1:
        child_bone = children[0]
        child_bone_name = child_bone.name
        child_transform_bone = arm.edit_bones.new(child_bone_name + ' transform')
        child_transform_bone.head = child_bone.head
        child_transform_bone.tail = child_bone.tail
        child_transform_bone.parent = target_bone
        subtarget_name = child_transform_bone.name
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='POSE')
        child_pose_bone = obj.pose.bones[child_bone_name]
        copy_rotation_constr = child_pose_bone.constraints.new('COPY_ROTATION')
        copy_rotation_constr.target = obj
        copy_rotation_constr.subtarget = subtarget_name
        copy_rotation_constr.enabled = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.select_all(action='DESELECT')
    pole_target_bone = arm.edit_bones.new(bone.name + ' pole_target')
    pole_target_bone.head = bone.head
    pole_target_bone.tail = bone.tail
    pole_target_bone.select = True
    pole_target_bone.select_head = True
    pole_target_bone.select_tail = True
    bpy.ops.transform.translate(
        value=(0.5, 0.0, 0.0),
        orient_type='NORMAL'
    )
    pole_target_bone.tail = pole_target_bone.head
    pole_target_bone.tail.z += 0.2
    pole_target_bone_name = pole_target_bone.name
    bpy.ops.object.mode_set(mode='POSE')
    ik_constr.pole_target = obj
    ik_constr.pole_subtarget = pole_target_bone_name
    ik_constr.pole_angle = math.radians(2)
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

    def execute(self, context):
        if not len(context.selected_pose_bones):
            self.report({'WARNING'}, text.warn.ik_no_selected_bones)
            return {'FINISHED'}
        for bone in context.selected_pose_bones:
            create_ik(bone, self.chain_length)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def register():
    version_utils.assign_props([(props, XRAY_OT_create_ik), ])
    bpy.utils.register_class(XRAY_OT_create_ik)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_create_ik)
