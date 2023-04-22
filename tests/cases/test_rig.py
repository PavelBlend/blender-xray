import bpy
import bmesh

import tests


class TestRig(tests.utils.XRayTestCase):
    def test_rig(self):
        arm_obj, me_obj = create_armature_object()

        # test connected bones without mesh
        bpy.ops.io_scene_xray.create_connected_bones(
            source_armature=arm_obj.name
        )

        # add armature modifier
        me_obj.parent = arm_obj
        arm_mode = me_obj.modifiers.new(name='Armature', type='ARMATURE')
        arm_mode.object = arm_obj

        # test connected bones with mesh
        bpy.ops.io_scene_xray.create_connected_bones(
            source_armature=arm_obj.name
        )

        # test create ik, foot test
        connected_obj = bpy.data.objects[arm_obj.name + ' connected']

        ik_obj = connected_obj.copy()
        ik_obj.data = connected_obj.data.copy()
        bpy.ops.object.select_all(action='DESELECT')
        tests.utils.link_object(ik_obj)
        tests.utils.set_active_object(ik_obj)

        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='DESELECT')
        ik_obj.pose.bones['foot_l c'].bone.select = True

        bpy.ops.io_scene_xray.create_ik()

        bpy.ops.object.mode_set(mode='OBJECT')

        # test create ik, knee test
        ik_obj = connected_obj.copy()
        ik_obj.data = connected_obj.data.copy()
        bpy.ops.object.select_all(action='DESELECT')
        tests.utils.link_object(ik_obj)
        tests.utils.set_active_object(ik_obj)

        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='DESELECT')
        ik_obj.pose.bones['knee_l c'].bone.select = True

        bpy.ops.io_scene_xray.create_ik()

        bpy.ops.object.mode_set(mode='OBJECT')


def create_armature_object():
    # create armature
    arm = bpy.data.armatures.new('test')
    arm_obj = bpy.data.objects.new('test', arm)

    tests.utils.link_object(arm_obj)
    tests.utils.set_active_object(arm_obj)

    bpy.ops.object.mode_set(mode='EDIT')

    root_height = 1.0
    floor_height = 0.0
    bone_length = 0.02
    leg_width = 0.2
    knee_offset = 0.1

    try:
        root_bone = arm.edit_bones.new('root')
        root_bone.tail.y = bone_length
        root_bone.tail.z = root_height
        root_bone.head.z = root_height

        leg_l_bone = arm.edit_bones.new('leg_l')
        leg_l_bone.parent = root_bone
        leg_l_bone.tail.x = -leg_width
        leg_l_bone.head.x = -leg_width
        leg_l_bone.tail.y = bone_length
        leg_l_bone.tail.z = root_height
        leg_l_bone.head.z = root_height

        leg_r_bone = arm.edit_bones.new('leg_r')
        leg_r_bone.parent = root_bone
        leg_r_bone.tail.x = leg_width
        leg_r_bone.head.x = leg_width
        leg_r_bone.tail.y = bone_length
        leg_r_bone.tail.z = root_height
        leg_r_bone.head.z = root_height

        knee_l_bone = arm.edit_bones.new('knee_l')
        knee_l_bone.parent = leg_l_bone
        knee_l_bone.tail.x = -leg_width
        knee_l_bone.head.x = -leg_width
        knee_l_bone.tail.y = knee_offset + bone_length
        knee_l_bone.head.y = knee_offset
        knee_l_bone.tail.z = root_height / 2
        knee_l_bone.head.z = root_height / 2

        knee_r_bone = arm.edit_bones.new('knee_r')
        knee_r_bone.parent = leg_r_bone
        knee_r_bone.tail.x = leg_width
        knee_r_bone.head.x = leg_width
        knee_r_bone.tail.y = knee_offset + bone_length
        knee_r_bone.head.y = knee_offset
        knee_r_bone.tail.z = root_height / 2
        knee_r_bone.head.z = root_height / 2

        foot_l_bone = arm.edit_bones.new('foot_l')
        foot_l_bone.parent = knee_l_bone
        foot_l_bone.tail.x = -leg_width
        foot_l_bone.head.x = -leg_width
        foot_l_bone.tail.y = bone_length
        foot_l_bone.tail.z = floor_height
        foot_l_bone.head.z = floor_height

        foor_r_bone = arm.edit_bones.new('foot_r')
        foor_r_bone.parent = knee_r_bone
        foor_r_bone.tail.x = leg_width
        foor_r_bone.head.x = leg_width
        foor_r_bone.tail.y = bone_length
        foor_r_bone.tail.z = floor_height
        foor_r_bone.head.z = floor_height

    finally:
        bpy.ops.object.mode_set(mode='OBJECT')

    # create mesh
    bm = bmesh.new()
    deform_layer = bm.verts.layers.deform.new('test')

    hip_l_verts = bmesh.ops.create_cube(bm, size=0.15)['verts']
    for vert in hip_l_verts:
        vert[deform_layer][0] = 1.0
        if vert.co.z > 0.0:
            vert.co.z = root_height
        else:
            vert.co.y += knee_offset
            vert.co.z = root_height / 2
    for vert in hip_l_verts:
        vert.co.x -= leg_width

    hip_r_verts = bmesh.ops.create_cube(bm, size=0.15)['verts']
    for vert in hip_r_verts:
        vert[deform_layer][1] = 1.0
        if vert.co.z > 0.0:
            vert.co.z = root_height
        else:
            vert.co.y += knee_offset
            vert.co.z = root_height / 2
    for vert in hip_r_verts:
        vert.co.x += leg_width

    caviar_l_verts = bmesh.ops.create_cube(bm, size=0.15)['verts']
    for vert in caviar_l_verts:
        vert[deform_layer][2] = 1.0
        if vert.co.z > 0.0:
            vert.co.y += knee_offset
            vert.co.z = root_height / 2
        else:
            vert.co.z = floor_height
    for vert in caviar_l_verts:
        vert.co.x -= leg_width

    caviar_r_verts = bmesh.ops.create_cube(bm, size=0.15)['verts']
    for vert in caviar_r_verts:
        vert[deform_layer][3] = 1.0
        if vert.co.z > 0.0:
            vert.co.y += knee_offset
            vert.co.z = root_height / 2
        else:
            vert.co.z = floor_height
    for vert in caviar_r_verts:
        vert.co.x += leg_width

    bm.verts.ensure_lookup_table()

    me = bpy.data.meshes.new('test')
    me_obj = bpy.data.objects.new('test', me)
    for group_name in ('leg_l', 'leg_r', 'knee_l', 'knee_r'):
        me_obj.vertex_groups.new(name=group_name)

    tests.utils.link_object(me_obj)
    tests.utils.set_active_object(me_obj)

    bm.to_mesh(me)

    return arm_obj, me_obj
