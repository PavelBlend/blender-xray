import bpy

from tests import utils


class TestAnmImport(utils.XRayTestCase):
    def test_add_camera(self):
        bpy.ops.io_scene_xray.add_camera()

    def test_change_action_bake_settings(self):
        for index in range(3):
            name = 'test_' + str(index)
            act = bpy.data.actions.new(name)
            obj = bpy.data.objects.new(name, None)
            obj.animation_data_create().action = act
            utils.link_object(obj)
            utils.select_object(obj)
            utils.set_active_object(obj)
            motion = obj.xray.motions_collection.add()
            motion.name = act.name
        for index in range(3, 6):
            name = 'test_' + str(index)
            act = bpy.data.actions.new(name)
            obj = bpy.data.objects.new(name, None)
            obj.animation_data_create().action = act
        for index in range(6, 9):
            name = 'test_' + str(index)
            act = bpy.data.actions.new(name)
        bpy.ops.io_scene_xray.change_action_bake_settings()
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ACTIVE_ACTION'
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ACTIVE_OBJECT'
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='SELECTED_OBJECTS'
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ALL_OBJECTS'
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ALL_ACTIONS'
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ALL_ACTIONS',
            change_auto_bake_mode=False
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ALL_ACTIONS',
            auto_bake_mode='auto'
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ALL_ACTIONS',
            auto_bake_mode='on'
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ALL_ACTIONS',
            auto_bake_mode='off'
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ALL_ACTIONS',
            change_use_custom_thresholds=False
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ALL_ACTIONS',
            use_custom_threshold=False
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ALL_ACTIONS',
            change_location_threshold=False
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ALL_ACTIONS',
            change_rotation_threshold=False
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ALL_ACTIONS',
            value_location_threshold=1.0
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ALL_ACTIONS',
            value_rotation_threshold=1.0
        )
