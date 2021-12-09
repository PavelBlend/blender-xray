# blender modules
import bpy

# addon modules
from .. import version_utils


props = {
    'source_armature': bpy.props.StringProperty(name='Source Armature'),
}
NAME_SUFFIX = ' connected'
BONE_NAME_SUFFIX = ' c'


def connect_bones(arm):
    bone_new_parent = {}
    for bone in arm.edit_bones:
        if len(bone.children) == 1:
            child_bone = bone.children[0]
            connected_bone = arm.edit_bones.new(name=bone.name + BONE_NAME_SUFFIX)
            connected_bone.head = bone.head
            connected_bone.tail = child_bone.head
            bone_new_parent[bone] = connected_bone
    bone_layers = [False, ] * 32
    old_bone_layers = bone_layers.copy()
    old_bone_layers[31] = True
    connected_bone_layers = bone_layers.copy()
    connected_bone_layers[0] = True
    for child_bone, parent_bone in bone_new_parent.items():
        old_parent = child_bone.parent
        child_bone.parent = parent_bone
        child_bone.layers = old_bone_layers
        new_parent = bone_new_parent.get(old_parent, None)
        if new_parent:
            parent_bone.parent = new_parent
        else:
            parent_bone.parent = old_parent


class XRAY_OT_connect_bones(bpy.types.Operator):
    bl_idname = 'io_scene_xray.connect_bones'
    bl_label = 'Connect Bones'
    bl_options = {'REGISTER', 'UNDO'}

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        split = version_utils.layout_split(self.layout, 0.35)
        split.label(text='Source Armature:')
        split.prop_search(self, 'source_armature', bpy.data, 'objects', text='')

    def execute(self, context):
        src_name = self.source_armature
        if not src_name:
            self.report({'WARNING'}, 'TEMP 1')
            return {'FINISHED'}
        src_arm_obj = bpy.data.objects.get(src_name)
        if not src_arm_obj:
            self.report({'WARNING'}, 'TEMP 2')
            return {'FINISHED'}
        if src_arm_obj.type != 'ARMATURE':
            self.report({'WARNING'}, 'TEMP 3')
            return {'FINISHED'}
        src_arm = src_arm_obj.data
        if not len(src_arm.bones):
            self.report({'WARNING'}, 'TEMP 4')
            return {'FINISHED'}
        arm_obj = src_arm_obj.copy()
        arm = src_arm.copy()
        arm_obj.data = arm
        arm_obj.name = src_arm_obj.name + NAME_SUFFIX
        arm.name = src_arm.name + NAME_SUFFIX
        version_utils.link_object(arm_obj)
        bpy.ops.object.select_all(action='DESELECT')
        version_utils.select_object(arm_obj)
        version_utils.set_active_object(arm_obj)
        bpy.ops.object.mode_set(mode='EDIT')
        connect_bones(arm)
        bpy.ops.object.mode_set(mode='OBJECT')
        # link bones
        version_utils.set_active_object(src_arm_obj)
        bpy.ops.io_scene_xray.link_bones(armature=arm_obj.name)
        version_utils.set_active_object(arm_obj)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def register():
    version_utils.assign_props([(props, XRAY_OT_connect_bones), ])
    bpy.utils.register_class(XRAY_OT_connect_bones)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_connect_bones)
