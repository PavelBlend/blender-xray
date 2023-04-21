# blender modules
import bpy
import mathutils

# addon modules
from .. import edit_helpers
from ... import utils
from ... import text


props = {
    'source_armature': bpy.props.StringProperty(name='Source Armature'),
}
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


def connect_bones(arm, mesh_objs):
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
    for bone in edit_bones:
        children_count = len(bone.children)
        connected_bone = arm.edit_bones.new(name=bone.name + BONE_NAME_SUFFIX)

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

        connected_bones[bone] = connected_bone

    # bone layers
    arm_layers = [False, ] * 32

    bone_layers = arm_layers.copy()
    bone_layers[31] = True

    connected_layers = arm_layers.copy()
    connected_layers[0] = True

    # change bones parents
    for bone, connected_bone in connected_bones.items():

        # set connected bone parent
        connected_parent = connected_bones.get(bone.parent, None)
        if connected_parent:
            connected_bone.parent = connected_parent
        else:
            connected_bone.parent = bone.parent

        # set bone parent
        bone.parent = connected_bone

        # set layers
        bone.layers = bone_layers
        connected_bone.layers = connected_layers

    bpy.ops.object.mode_set(mode='OBJECT')


class XRAY_OT_create_connected_bones(utils.ie.BaseOperator):
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
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # check input
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

        # create armature
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
        connect_bones(arm, mesh_objects)

        # create weights bones
        create_weights_bones(src_arm_obj, arm_obj)

        # link bones
        utils.version.set_active_object(src_arm_obj)
        bpy.ops.io_scene_xray.link_bones(armature=arm_obj.name)
        utils.version.set_active_object(arm_obj)

        self.report({'INFO'}, text.get_text(text.warn.ready))

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def register():
    utils.version.assign_props([(props, XRAY_OT_create_connected_bones), ])
    bpy.utils.register_class(XRAY_OT_create_connected_bones)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_create_connected_bones)
