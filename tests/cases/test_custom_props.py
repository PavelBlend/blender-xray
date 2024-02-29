import bpy
import tests


class TestCustomProps(tests.utils.XRayTestCase):
    def test_default(self):
        me_obj, arm_obj = self.create_objects()

        # all all
        bpy.ops.io_scene_xray.set_xray_to_custom_properties(
            props={'ALL'},
            mode='ALL'
        )
        bpy.ops.io_scene_xray.set_custom_to_xray_properties(
            props={'ALL'},
            mode='ALL'
        )
        bpy.ops.io_scene_xray.remove_xray_custom_props(
            props={'ALL'},
            mode='ALL'
        )
        bpy.ops.io_scene_xray.remove_all_custom_props(
            props={'ALL'},
            mode='ALL'
        )

        # all selected
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.io_scene_xray.set_xray_to_custom_properties(
            props={'ALL'},
            mode='SELECTED'
        )
        bpy.ops.io_scene_xray.set_custom_to_xray_properties(
            props={'ALL'},
            mode='SELECTED'
        )
        bpy.ops.io_scene_xray.remove_all_custom_props(
            props={'ALL'},
            mode='SELECTED'
        )
        bpy.ops.io_scene_xray.remove_xray_custom_props(
            props={'ALL'},
            mode='SELECTED'
        )

        # all active
        tests.utils.set_active_object(me_obj)
        bpy.ops.io_scene_xray.set_xray_to_custom_properties(
            props={'ALL'},
            mode='ACTIVE'
        )
        bpy.ops.io_scene_xray.set_custom_to_xray_properties(
            props={'ALL'},
            mode='ACTIVE'
        )
        bpy.ops.io_scene_xray.remove_xray_custom_props(
            props={'ALL'},
            mode='ACTIVE'
        )
        bpy.ops.io_scene_xray.remove_all_custom_props(
            props={'ALL'},
            mode='ACTIVE'
        )

        # object all
        bpy.ops.io_scene_xray.set_xray_to_custom_properties(
            props={'OBJECT'},
            mode='ALL'
        )
        bpy.ops.io_scene_xray.set_custom_to_xray_properties(
            props={'OBJECT'},
            mode='ALL'
        )
        bpy.ops.io_scene_xray.remove_xray_custom_props(
            props={'OBJECT'},
            mode='ALL'
        )
        bpy.ops.io_scene_xray.remove_all_custom_props(
            props={'OBJECT'},
            mode='ALL'
        )

        # mesh active
        tests.utils.set_active_object(None)
        bpy.ops.io_scene_xray.set_xray_to_custom_properties(
            props={'MESH'},
            mode='ACTIVE'
        )
        bpy.ops.io_scene_xray.set_custom_to_xray_properties(
            props={'MESH'},
            mode='ACTIVE'
        )
        bpy.ops.io_scene_xray.remove_xray_custom_props(
            props={'MESH'},
            mode='ACTIVE'
        )
        bpy.ops.io_scene_xray.remove_all_custom_props(
            props={'MESH'},
            mode='ACTIVE'
        )

        # material active
        bpy.ops.io_scene_xray.set_xray_to_custom_properties(
            props={'MATERIAL'},
            mode='ACTIVE'
        )
        bpy.ops.io_scene_xray.set_custom_to_xray_properties(
            props={'MATERIAL'},
            mode='ACTIVE'
        )

        # material all
        bpy.ops.io_scene_xray.set_xray_to_custom_properties(
            props={'MATERIAL'},
            mode='ALL'
        )
        bpy.ops.io_scene_xray.set_custom_to_xray_properties(
            props={'MATERIAL'},
            mode='ALL'
        )

        # bone active
        tests.utils.set_active_object(arm_obj)
        bpy.ops.io_scene_xray.set_xray_to_custom_properties(
            props={'BONE'},
            mode='ACTIVE'
        )
        bpy.ops.io_scene_xray.set_custom_to_xray_properties(
            props={'BONE'},
            mode='ACTIVE'
        )

        # action all
        bpy.ops.io_scene_xray.set_xray_to_custom_properties(
            props={'ACTION'},
            mode='ALL'
        )
        bpy.ops.io_scene_xray.set_custom_to_xray_properties(
            props={'ACTION'},
            mode='ALL'
        )

    def create_objects(self):
        name = 'test_custom_props'

        # create mesh
        me = bpy.data.meshes.new(name)
        me_ob = bpy.data.objects.new(name, me)
        tests.utils.link_object(me_ob)
        me.from_pydata(
            ((0, 0, 0), (1, 0, 0), (1, 1, 0)),
            (),
            ((0, 1, 2), )
        )
        motion = me_ob.xray.motionrefs_collection.add()
        motion.name = name

        # create material
        mt = bpy.data.materials.new(name)
        me.materials.append(mt)
        mt.xray.eshader = name
        mt.xray.cshader = name
        mt.xray.gamemtl = name

        # create armature
        arm = bpy.data.armatures.new(name)
        arm_ob = bpy.data.objects.new(name, arm)
        bpy.ops.object.select_all(action='DESELECT')
        tests.utils.link_object(arm_ob)
        tests.utils.set_active_object(arm_ob)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.bone_primitive_add()
        bpy.ops.object.mode_set(mode='OBJECT')
        arm.bones[0].name = 'test_bone'
        arm.bones[1].xray.exportable = False
        mod = me_ob.modifiers.new('test', 'ARMATURE')
        mod.object = arm_ob
        me_ob.parent = arm_ob
        bone_group = arm_ob.pose.bone_groups.new(name=name)
        arm_ob.pose.bones[0].bone_group = bone_group

        # create action
        act = bpy.data.actions.new(name)
        arm_ob.animation_data_create()
        arm_ob.animation_data.action = act
        motion = arm_ob.xray.motions_collection.add()
        motion.name = act.name

        return me_ob, arm_ob
