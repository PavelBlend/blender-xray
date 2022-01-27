# blender modules
import bpy

# addon modules
from .. import utils
from .. import version_utils


COPY_TRANSFORMS_NAME = '!-xray-link'

op_props = {
    'armature': bpy.props.StringProperty(name='Link to'),
}


class XRAY_OT_link_bones(bpy.types.Operator):
    bl_idname = 'io_scene_xray.link_bones'
    bl_label = 'Link Bones'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    props = op_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        if context.object.type == 'ARMATURE':
            return True

    def draw(self, context):
        self.layout.prop_search(self, 'armature', bpy.data, 'objects')

    @utils.set_cursor_state
    def execute(self, context):
        arm_obj = context.object
        link_arm_obj = bpy.data.objects.get(self.armature)
        if arm_obj.type != 'ARMATURE':
            return {'FINISHED'}
        if not link_arm_obj:
            return {'FINISHED'}
        if link_arm_obj.type != 'ARMATURE':
            return {'FINISHED'}
        if arm_obj.name == self.armature:
            return {'FINISHED'}
        for link_bone in link_arm_obj.data.bones:
            bone = arm_obj.data.bones.get(link_bone.name)
            if not bone:
                continue
            pose_bone = arm_obj.pose.bones[bone.name]
            constraint = pose_bone.constraints.get(COPY_TRANSFORMS_NAME)
            if not constraint:
                constraint = pose_bone.constraints.new('COPY_TRANSFORMS')
                constraint.name = COPY_TRANSFORMS_NAME
            constraint.target = link_arm_obj
            constraint.subtarget = link_bone.name
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_unlink_bones(bpy.types.Operator):
    bl_idname = 'io_scene_xray.unlink_bones'
    bl_label = 'Unlink Bones'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        if context.object.type == 'ARMATURE':
            return True

    @utils.set_cursor_state
    def execute(self, context):
        arm_obj = context.object
        for bone in arm_obj.data.bones:
            pose_bone = arm_obj.pose.bones[bone.name]
            constraint = pose_bone.constraints.get(COPY_TRANSFORMS_NAME)
            if not constraint:
                continue
            pose_bone.constraints.remove(constraint)
        return {'FINISHED'}


classes = (
    XRAY_OT_link_bones,
    XRAY_OT_unlink_bones
)


def register():
    version_utils.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
