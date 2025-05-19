# blender modules
import bpy
import mathutils

# addon modules
from .. import edit_helpers
from ... import utils
from ... import text


NAME_SUFFIX = ' connected'
WEIGHT_SUFFIX = ' weight'
BONE_NAME_SUFFIX = ' c'


def create_weights_bones(src_arm_obj, con_arm_obj):
    # create weight armature
    weight_arm = src_arm_obj.data.copy()
    weight_arm.name = src_arm_obj.data.name + WEIGHT_SUFFIX

    weight_obj = src_arm_obj.copy()
    weight_obj.name = src_arm_obj.name + WEIGHT_SUFFIX

    weight_obj.data = weight_arm
    utils.version.link_object(weight_obj)

    # change xray properties
    weight_obj.xray.isroot = False

    # collect connected bones transforms
    transforms = {}

    utils.version.set_active_object(con_arm_obj)
    bpy.ops.object.mode_set(mode='EDIT')

    for bone in con_arm_obj.data.edit_bones:
        transforms[bone.name] = (bone.head.copy(), bone.tail.copy(), bone.roll)

    bpy.ops.object.mode_set(mode='OBJECT')

    # set weight bones transforms
    utils.version.set_active_object(weight_obj)
    bpy.ops.object.mode_set(mode='EDIT')

    for edit_bone in weight_obj.data.edit_bones:
        con_name = edit_bone.name + BONE_NAME_SUFFIX
        if transforms.get(con_name):
            head, tail, roll = transforms[con_name]
            edit_bone.head = head
            edit_bone.tail = tail
            edit_bone.roll = roll

    bpy.ops.object.mode_set(mode='OBJECT')

    # collect source shape matrices and mass centers
    utils.version.set_active_object(src_arm_obj)
    bpy.ops.object.mode_set(mode='POSE')

    scr_shape_mats = {}
    scr_mass_mats = {}
    for src_bone in src_arm_obj.data.bones:
        src_pose_bone = src_arm_obj.pose.bones[src_bone.name]
        edit_helpers.bone_shape.pose_bone = src_pose_bone

        shape = src_bone.xray.shape
        shape_type = shape.type

        matrices = {}
        for shape_type_id in range(1, 4):
            shape.type = str(shape_type_id)
            shape_mat = edit_helpers.bone_shape.bone_matrix(src_bone)
            matrices[shape_type_id] = shape_mat
        mass_mat = edit_helpers.bone_center.get_mass_matrix(src_bone)
        scr_shape_mats[src_bone.name] = matrices
        scr_mass_mats[src_bone.name] = mass_mat

        shape.type = shape_type

    bpy.ops.object.mode_set(mode='OBJECT')

    # set weight bone shapes
    utils.version.set_active_object(weight_obj)
    bpy.ops.object.mode_set(mode='POSE')

    for wght_bone in weight_obj.data.bones:
        src_bone = src_arm_obj.data.bones[wght_bone.name]
        wght_pose_bone = weight_obj.pose.bones[wght_bone.name]

        edit_helpers.bone_shape.pose_bone = wght_pose_bone

        src_shape = src_bone.xray.shape
        wght_shape = wght_bone.xray.shape

        for shape_type_id in range(1, 4):
            wght_shape.type = str(shape_type_id)
            mat = scr_shape_mats[wght_bone.name][shape_type_id]

            edit_helpers.bone_shape.apply_shape(wght_bone, mat)

        mass_mat = scr_mass_mats[wght_bone.name]
        edit_helpers.bone_center.pose_bone = wght_pose_bone
        edit_helpers.bone_center.apply_mass_matrix(wght_bone, mass_mat)

        wght_shape.type = src_shape.type
        wght_shape.box_hsz = src_shape.box_hsz

    bpy.ops.object.mode_set(mode='OBJECT')


def set_con_tail_without_verts(bone, connected_bone):
    # set connected bone tail without vertices
    parent = bone.parent
    if parent:
        offset = (parent.head - bone.head).length / 2
        direct = (bone.head - parent.head).normalized()
        tail_offset = direct * offset
    else:
        offset = 0.05
        tail_offset = mathutils.Vector((0, 0, offset))
    connected_bone.tail = connected_bone.head + tail_offset


def connect_bones(obj, arm, mesh_objs):
    bpy.ops.object.mode_set(mode='EDIT')

    # collect vertex groups
    vertex_groups = {}
    for mesh_obj in mesh_objs:
        for vertex in mesh_obj.data.vertices:
            for group in vertex.groups:
                vert_group = mesh_obj.vertex_groups[group.group]
                vertex_groups.setdefault(vert_group.name, []).append((
                    vertex.co,
                    group.weight
                ))

    # collect edit bones
    edit_bones = []
    for bone in arm.edit_bones:
        edit_bones.append(bone)

    # create connected bones
    connected_bones = {}
    connected_bone_names = []
    connected_bone_table = {}
    for bone in edit_bones:
        children_count = len(bone.children)
        connected_bone = arm.edit_bones.new(name=bone.name + BONE_NAME_SUFFIX)
        connected_bone_names.append(connected_bone.name)

        # set head coordinate
        connected_bone.head = bone.head

        # set tail coordinate
        if children_count == 1:    # one child
            child_bone = bone.children[0]
            connected_bone.tail = child_bone.head

        elif children_count > 1:    # many children
            children_sum = mathutils.Vector((0.0, 0.0, 0.0))
            for child_bone in bone.children:
                children_sum += child_bone.head
            children_center = children_sum / len(bone.children)
            connected_bone.tail = (connected_bone.head + children_center) / 2

        else:    # without children
            if mesh_objs:
                vertices = vertex_groups.get(bone.name)
                if vertices:
                    verts_sum = mathutils.Vector((0.0, 0.0, 0.0))
                    for vert_co, weight in vertices:
                        verts_sum += (vert_co - connected_bone.head) * weight
                    tail_offset = verts_sum / len(vertices)
                    connected_bone.tail = connected_bone.head + tail_offset
                else:
                    set_con_tail_without_verts(bone, connected_bone)

            else:
                set_con_tail_without_verts(bone, connected_bone)

        if connected_bone.head == connected_bone.tail:
            connected_bone.tail.z += 0.01

        connected_bones[bone] = connected_bone
        connected_bone_table[bone.name] = connected_bone.name

    # create connected bones 2
    bpy.ops.object.mode_set(mode='OBJECT')
    obj_2, arm_2 = _copy_arm_obj(obj, '_2')

    bpy.ops.object.mode_set(mode='EDIT')

    # change parents for connected 2 bones
    for bone_name, connected_bone_name in connected_bone_table.items():
        bone = arm_2.edit_bones[bone_name]
        connected_bone = arm_2.edit_bones[connected_bone_name]

        # set bone parent
        connected_bone.parent = bone

        # set layers
        utils.version.set_deform_layer(arm_2, connected_bone)
        utils.version.set_first_layer(arm_2, bone)

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    utils.version.select_object(obj)
    utils.version.set_active_object(obj)
    bpy.ops.object.mode_set(mode='EDIT')

    # change bones parents
    for bone_name, connected_bone_name in connected_bone_table.items():
        bone = arm.edit_bones[bone_name]
        connected_bone = arm.edit_bones[connected_bone_name]

        # set connected bone parent
        connected_parent_name = connected_bone_table.get(bone.parent, None)
        if connected_parent_name:
            connected_parent = arm.edit_bones[connected_parent_name]
            connected_bone.parent = connected_parent
        else:
            connected_bone.parent = bone.parent

        # set bone parent
        bone.parent = connected_bone

        # set layers
        utils.version.set_deform_layer(arm, bone)
        utils.version.set_first_layer(arm, connected_bone)

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    # set exportable
    for name in connected_bone_names:
        bone = arm.bones.get(name)
        if bone:
            bone.xray.exportable = False


def _copy_arm_obj(src_arm_obj, name_suffix):
    arm_obj = src_arm_obj.copy()
    src_arm = src_arm_obj.data
    arm = src_arm.copy()
    arm_obj.data = arm
    arm_obj.name = src_arm_obj.name + name_suffix
    arm.name = src_arm.name + name_suffix
    utils.version.link_object(arm_obj)
    bpy.ops.object.select_all(action='DESELECT')
    utils.version.select_object(arm_obj)
    utils.version.set_active_object(arm_obj)
    return arm_obj, arm


class XRAY_OT_create_connected_bones(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.create_connected_bones'
    bl_label = 'Create Connected Bones'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        active = context.active_object
        return active and active.type == 'ARMATURE'

    @utils.set_cursor_state
    def execute(self, context):

        # check input
        src_arm_obj = context.active_object
        if not src_arm_obj:
            self.report({'WARNING'}, text.error.no_active_obj)
            return {'FINISHED'}

        if src_arm_obj.type != 'ARMATURE':
            self.report({'WARNING'}, text.error.is_not_arm)
            return {'FINISHED'}

        src_arm = src_arm_obj.data
        if not len(src_arm.bones):
            self.report({'WARNING'}, text.warn.connect_has_no_bones)
            return {'FINISHED'}

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # remove current animation data
        if src_arm_obj.animation_data:
            src_arm_obj.animation_data.action = None

        # reset bones transforms
        utils.bone.reset_pose_bone_transforms(src_arm_obj)

        # create armature
        arm_obj, arm = _copy_arm_obj(src_arm_obj, NAME_SUFFIX)

        # change xray properties
        arm_obj.xray.isroot = False

        # clear pose bone transforms
        bpy.ops.object.mode_set(mode='POSE')
        for bone in arm_obj.pose.bones:
            bone.matrix_basis = mathutils.Matrix.Identity(4)

        # collect meshes
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

        # connect bones
        connect_bones(arm_obj, arm, mesh_objects)

        # create weights bones
        create_weights_bones(src_arm_obj, arm_obj)

        # link bones
        utils.version.set_active_object(src_arm_obj)
        bpy.ops.io_scene_xray.link_bones(armature=arm_obj.name)
        utils.version.set_active_object(arm_obj)

        # report
        self.report({'INFO'}, text.warn.ready)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(XRAY_OT_create_connected_bones)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_create_connected_bones)
