# blender modules
import bpy
import mathutils

# addon modules
from .. import utils
from .. import text


props = {
    'source_armature': bpy.props.StringProperty(name='Source Armature'),
}
NAME_SUFFIX = ' connected'
BONE_NAME_SUFFIX = ' c'


def connect_bones(arm, mesh_objs):
    bone_new_parent = {}
    vertex_groups = {}
    if mesh_objs:
        for bone in arm.edit_bones:
            if not len(bone.children):
                for mesh_obj in mesh_objs:
                    for vertex in mesh_obj.data.vertices:
                        for group in vertex.groups:
                            vertex_group = mesh_obj.vertex_groups[group.group]
                            vertex_groups.setdefault(vertex_group.name, []).append((
                                vertex.co,
                                group.weight
                            ))
    edit_bones = []
    for bone in arm.edit_bones:
        edit_bones.append(bone)
    for bone in edit_bones:
        children_count = len(bone.children)
        connected_bone = arm.edit_bones.new(name=bone.name + BONE_NAME_SUFFIX)
        connected_bone.head = bone.head
        if children_count == 1:
            child_bone = bone.children[0]
            connected_bone.tail = child_bone.head
        elif children_count > 1:
            children_heads = []
            for child_bone in bone.children:
                children_heads.append(child_bone.head)
            children_sum = mathutils.Vector((0.0, 0.0, 0.0))
            for child_head in children_heads:
                children_sum += child_head
            children_center = children_sum / len(children_heads)
            connected_bone.tail = (children_center + bone.head) / 2
        elif not children_count:
            if mesh_objs:
                vertices = vertex_groups.get(bone.name)
                if not vertices:
                    continue
                vertex_sum_offset = mathutils.Vector((0.0, 0.0, 0.0))
                weights = []
                for vert_co, weight in vertices:
                    vertex_sum_offset += (vert_co - connected_bone.head) * weight
                    weights.append(weight)
                tail_offset = vertex_sum_offset / sum(weights)
                connected_bone.tail = connected_bone.head + tail_offset
            else:
                parent = bone.parent
                if parent:
                    offset = (parent.head - bone.head).length / 2
                    direct = (bone.head - parent.head).normalized()
                    tail_offset = direct * offset
                else:
                    offset = 0.05
                    tail_offset = mathutils.Vector((0, 0, offset))
                connected_bone.tail = connected_bone.head + tail_offset
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


class XRAY_OT_create_connected_bones(bpy.types.Operator):
    bl_idname = 'io_scene_xray.create_connected_bones'
    bl_label = 'Create Connected Bones'
    bl_options = {'REGISTER', 'UNDO'}

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        split = utils.version.layout_split(self.layout, 0.35)
        split.label(text='Source Armature:')
        split.prop_search(self, 'source_armature', bpy.data, 'objects', text='')

    @utils.set_cursor_state
    def execute(self, context):
        if context.object:
            bpy.ops.object.mode_set(mode='OBJECT')
        src_name = self.source_armature
        if not src_name:
            self.report({'WARNING'}, text.warn.connect_not_spec_arm)
            return {'FINISHED'}
        src_arm_obj = bpy.data.objects.get(src_name)
        if not src_arm_obj:
            self.report({'WARNING'}, text.warn.connect_not_found_arm)
            return {'FINISHED'}
        if src_arm_obj.type != 'ARMATURE':
            self.report({'WARNING'}, text.warn.connect_is_not_arm)
            return {'FINISHED'}
        src_arm = src_arm_obj.data
        if not len(src_arm.bones):
            self.report({'WARNING'}, text.warn.connect_nas_no_bones)
            return {'FINISHED'}
        arm_obj = src_arm_obj.copy()
        arm = src_arm.copy()
        arm_obj.data = arm
        arm_obj.name = src_arm_obj.name + NAME_SUFFIX
        arm.name = src_arm.name + NAME_SUFFIX
        utils.version.link_object(arm_obj)
        bpy.ops.object.select_all(action='DESELECT')
        utils.version.select_object(arm_obj)
        utils.version.set_active_object(arm_obj)
        # clear pose bone transforms
        bpy.ops.object.mode_set(mode='POSE')
        for bone in arm_obj.pose.bones:
            bone.matrix_basis = mathutils.Matrix.Identity(4)
        arm_user_map = bpy.data.user_map(
            subset={src_arm_obj, },
            value_types={'OBJECT', }
        )
        object_users = list(arm_user_map[src_arm_obj])
        mesh_objects = []
        if object_users:
            for obj in object_users:
                if obj.type == 'MESH':
                    mesh_objects.append(obj)
        bpy.ops.object.mode_set(mode='EDIT')
        connect_bones(arm, mesh_objects)
        bpy.ops.object.mode_set(mode='OBJECT')
        # link bones
        utils.version.set_active_object(src_arm_obj)
        bpy.ops.io_scene_xray.link_bones(armature=arm_obj.name)
        utils.version.set_active_object(arm_obj)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def register():
    utils.version.assign_props([(props, XRAY_OT_create_connected_bones), ])
    bpy.utils.register_class(XRAY_OT_create_connected_bones)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_create_connected_bones)
