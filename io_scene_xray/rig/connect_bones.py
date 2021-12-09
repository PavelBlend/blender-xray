# blender modules
import bpy
import mathutils

# addon modules
from .. import version_utils


props = {
    'source_armature': bpy.props.StringProperty(name='Source Armature'),
}
NAME_SUFFIX = ' connected'
BONE_NAME_SUFFIX = ' c'


def connect_bones(arm, mesh_obj):
    bone_new_parent = {}
    mesh = mesh_obj.data
    vertex_groups = {}
    for bone in arm.edit_bones:
        children_count = len(bone.children)
        if not children_count:
            for vertex_index, vertex in enumerate(mesh.vertices):
                for group in vertex.groups:
                    vertex_group = mesh_obj.vertex_groups[group.group]
                    vertex_groups.setdefault(vertex_group.name, []).append(vertex_index)
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
            vertices = vertex_groups.get(bone.name)
            if not vertices:
                continue
            vertex_group = mesh_obj.vertex_groups[bone.name]
            group_index = vertex_group.index
            vertex_sum_offset = mathutils.Vector((0.0, 0.0, 0.0))
            weights = []
            for vertex_index in vertices:
                vertex = mesh.vertices[vertex_index]
                for group in vertex.groups:
                    if group.group == group_index:
                        vertex_sum_offset += (vertex.co - connected_bone.head) * group.weight
                        weights.append(group.weight)
            tail_offset = vertex_sum_offset / sum(weights)
            connected_bone.tail = connected_bone.head + tail_offset * 2
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
        bpy.ops.object.mode_set(mode='OBJECT')
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
        if mesh_objects:
            mesh = mesh_objects[0]
        else:
            mesh = None
        bpy.ops.object.mode_set(mode='EDIT')
        connect_bones(arm, mesh)
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
