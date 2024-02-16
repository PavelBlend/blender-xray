import os
import re
import bpy
import tests
import io_scene_xray


class TestOps(tests.utils.XRayTestCase):
    def test_add_camera(self):
        bpy.ops.io_scene_xray.add_camera(camera_type='HUD')
        bpy.ops.io_scene_xray.add_camera(camera_type='LEVEL')

    def test_change_action_bake_settings(self):
        # without objects test
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ACTIVE_ACTION'
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ACTIVE_OBJECT'
        )

        # without anim data test
        obj = bpy.data.objects.new('test_obj', None)
        tests.utils.link_object(obj)
        tests.utils.select_object(obj)
        tests.utils.set_active_object(obj)

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
        tests.utils.remove_object(obj)

        # without motions test
        obj = bpy.data.objects.new('test_obj', None)
        tests.utils.link_object(obj)
        tests.utils.select_object(obj)
        tests.utils.set_active_object(obj)
        obj.animation_data_create()

        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ACTIVE_ACTION'
        )
        tests.utils.remove_object(obj)

        # without actions test
        obj = bpy.data.objects.new('test_obj', None)
        tests.utils.link_object(obj)
        tests.utils.select_object(obj)
        tests.utils.set_active_object(obj)
        motion = obj.xray.motions_collection.add()
        motion.name = 'test_motion'

        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ACTIVE_OBJECT'
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='SELECTED_OBJECTS'
        )
        bpy.ops.io_scene_xray.change_action_bake_settings(
            change_mode='ALL_OBJECTS'
        )
        tests.utils.remove_object(obj)

        for index in range(3):
            name = 'test_' + str(index)
            act = bpy.data.actions.new(name)
            obj = bpy.data.objects.new(name, None)
            obj.animation_data_create().action = act
            tests.utils.link_object(obj)
            tests.utils.select_object(obj)
            tests.utils.set_active_object(obj)
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

    def test_copy_paste_action_settings(self):
        # test without object
        bpy.ops.io_scene_xray.copy_action_settings()
        bpy.ops.io_scene_xray.paste_action_settings()

        # test without anim data
        arm = bpy.data.armatures.new('test_arm')
        obj = bpy.data.objects.new('test_obj', arm)
        tests.utils.link_object(obj)
        tests.utils.select_object(obj)
        tests.utils.set_active_object(obj)
        bpy.ops.io_scene_xray.copy_action_settings()
        bpy.ops.io_scene_xray.paste_action_settings()

        # copy
        act = bpy.data.actions.new('test_act_copy')
        arm = bpy.data.armatures.new('test_arm_copy')
        obj = bpy.data.objects.new('test_obj_copy', arm)
        obj.animation_data_create().action = act
        tests.utils.link_object(obj)
        tests.utils.select_object(obj)
        tests.utils.set_active_object(obj)
        bpy.ops.io_scene_xray.copy_action_settings()

        # paste
        act = bpy.data.actions.new('test_act_paste')
        arm = bpy.data.armatures.new('test_arm_paste')
        obj = bpy.data.objects.new('test_obj_paste', arm)
        obj.animation_data_create().action = act
        tests.utils.link_object(obj)
        tests.utils.select_object(obj)
        tests.utils.set_active_object(obj)
        bpy.ops.io_scene_xray.paste_action_settings()

    def test_rename_actions(self):
        tests.utils.remove_all_objects()

        # without objects test
        bpy.ops.io_scene_xray.rename_actions(
            data_mode='ACTIVE_MOTION',

            part_1='OBJECT_NAME',
            prefix_1='',
            suffix_1='',
            function_1='NONE',
            replace_old_1='',
            replace_new_1='',

            part_2='MOTION_NAME',
            prefix_2='',
            suffix_2='',
            function_2='NONE',
            replace_old_2='',
            replace_new_2=''
        )
        self.assertReportsContains('WARNING', re.compile('No active object'))

        # without motions test
        arm = bpy.data.armatures.new('test_arm')
        obj = bpy.data.objects.new('test_obj', arm)
        tests.utils.link_object(obj)
        tests.utils.select_object(obj)
        tests.utils.set_active_object(obj)

        bpy.ops.io_scene_xray.rename_actions(
            data_mode='ACTIVE_MOTION',

            part_1='OBJECT_NAME',
            prefix_1='',
            suffix_1='',
            function_1='NONE',
            replace_old_1='',
            replace_new_1='',

            part_2='MOTION_NAME',
            prefix_2='',
            suffix_2='',
            function_2='NONE',
            replace_old_2='',
            replace_new_2=''
        )
        self.assertReportsContains(
            'INFO',
            re.compile('Renamed: 0, Not Renamed: 0')
        )
        tests.utils.remove_object(obj)

        # without action test
        arm = bpy.data.armatures.new('test_arm')
        obj = bpy.data.objects.new('test_obj', arm)
        tests.utils.link_object(obj)
        tests.utils.select_object(obj)
        tests.utils.set_active_object(obj)
        motion = obj.xray.motions_collection.add()
        motion.name = 'test_motion'

        bpy.ops.io_scene_xray.rename_actions(
            data_mode='ACTIVE_MOTION',

            part_1='OBJECT_NAME',
            prefix_1='',
            suffix_1='',
            function_1='NONE',
            replace_old_1='',
            replace_new_1='',

            part_2='MOTION_NAME',
            prefix_2='',
            suffix_2='',
            function_2='NONE',
            replace_old_2='',
            replace_new_2=''
        )
        self.assertReportsContains(
            'INFO',
            re.compile('Renamed: 0, Not Renamed: 0')
        )
        tests.utils.remove_object(obj)

        # long name test
        arm = bpy.data.armatures.new('test_arm')
        obj = bpy.data.objects.new('a' * 63, arm)
        tests.utils.link_object(obj)
        tests.utils.select_object(obj)
        tests.utils.set_active_object(obj)
        act = bpy.data.actions.new('b' * 63)
        obj.animation_data_create().action = act
        motion = obj.xray.motions_collection.add()
        motion.name = act.name

        bpy.ops.io_scene_xray.rename_actions(
            data_mode='ACTIVE_MOTION',

            part_1='OBJECT_NAME',
            prefix_1='',
            suffix_1='',
            function_1='NONE',
            replace_old_1='',
            replace_new_1='',

            part_2='MOTION_NAME',
            prefix_2='',
            suffix_2='',
            function_2='NONE',
            replace_old_2='',
            replace_new_2=''
        )
        self.assertReportsContains(
            'INFO',
            re.compile('Renamed: 0, Not Renamed: 0')
        )
        tests.utils.remove_object(obj)

        # Arrange
        for obj_index in range(3):
            arm = bpy.data.armatures.new('test_arm_{}'.format(obj_index))
            obj = bpy.data.objects.new('test_obj_{}'.format(obj_index), arm)
            tests.utils.link_object(obj)
            tests.utils.select_object(obj)
            tests.utils.set_active_object(obj)
            for act_index in range(3):
                act = bpy.data.actions.new('test_act_{}'.format(act_index))
                obj.animation_data_create().action = act
                motion = obj.xray.motions_collection.add()
                motion.name = act.name

        # Act
        bpy.ops.io_scene_xray.rename_actions(
            data_mode='ACTIVE_MOTION',

            part_1='OBJECT_NAME',
            prefix_1='',
            suffix_1='',
            function_1='NONE',
            replace_old_1='',
            replace_new_1='',

            part_2='MOTION_NAME',
            prefix_2='',
            suffix_2='',
            function_2='NONE',
            replace_old_2='',
            replace_new_2=''
        )
        bpy.ops.io_scene_xray.rename_actions(
            data_mode='ACTIVE_OBJECT',

            part_1='OBJECT_NAME',
            prefix_1='prefix_',
            suffix_1='_suffix',
            function_1='LOWER',
            replace_old_1='_',
            replace_new_1='-',

            part_2='MOTION_NAME',
            prefix_2='p',
            suffix_2='s',
            function_2='UPPER',
            replace_old_2='test_',
            replace_new_2='new_'
        )
        bpy.ops.io_scene_xray.rename_actions(
            data_mode='SELECTED_OBJECTS',

            part_1='OBJECT_NAME',
            prefix_1='',
            suffix_1='',
            function_1='CAPITALIZE',
            replace_old_1='',
            replace_new_1='',

            part_2='MOTION_NAME',
            prefix_2='',
            suffix_2='',
            function_2='TITLE',
            replace_old_2='',
            replace_new_2=''
        )
        bpy.ops.io_scene_xray.rename_actions(
            data_mode='ALL_OBJECTS',

            part_1='NONE',
            prefix_1='',
            suffix_1='',
            function_1='NONE',
            replace_old_1='',
            replace_new_1='',

            part_2='MOTION_NAME',
            prefix_2='',
            suffix_2='',
            function_2='NONE',
            replace_old_2='',
            replace_new_2=''
        )
        bpy.ops.io_scene_xray.rename_actions(
            data_mode='ALL_OBJECTS',

            part_1='MOTION_NAME',
            prefix_1='',
            suffix_1='',
            function_1='NONE',
            replace_old_1='',
            replace_new_1='',

            part_2='NONE',
            prefix_2='',
            suffix_2='',
            function_2='NONE',
            replace_old_2='',
            replace_new_2=''
        )

    def test_verify_uv(self):
        # test without selected objects
        bpy.ops.io_scene_xray.verify_uv()

        verts = [
            [0, 0, 0],
            [1, 0, 0],
            [1, 1, 0],
            [0, 1, 0]
        ]
        faces = (
            (0, 1, 2),
            (2, 3, 0)
        )
        uvs = [
            0, 0,
            1, 0,
            1, 1,
            1, 1,
            0, 1,
            0, 0
        ]
        uv_offsets = (
            (0, 0),
            (50, 50),
            (-1, -1)
        )
        for i in range(3):
            mesh = bpy.data.meshes.new('test_verify_uv')
            mesh.from_pydata(verts, (), faces)
            if bpy.app.version >= (2, 80, 0):
                uv_layer = mesh.uv_layers.new(name='uv')
            else:
                uv_tex = mesh.uv_textures.new(name='uv')
                uv_layer = mesh.uv_layers[uv_tex.name]
            obj = bpy.data.objects.new('test_verify_uv_{}'.format(i), mesh)
            tests.utils.link_object(obj)
            tests.utils.select_object(obj)
            for vert in verts:
                vert[0] += 2
            uv_offset_x, uv_offset_y = uv_offsets[i]
            current_uvs = uvs.copy()
            for uv_index in range(0, len(current_uvs), 2):
                current_uvs[uv_index] += uv_offset_x
                current_uvs[uv_index + 1] += uv_offset_y
            uv_layer.data.foreach_set('uv', current_uvs)
        obj = bpy.data.objects.new('test_verify_uv_empty', None)
        tests.utils.link_object(obj)
        tests.utils.select_object(obj)
        bpy.ops.io_scene_xray.verify_uv()

        self.assertEqual(len(bpy.context.selected_objects), 1)

        bpy.ops.object.select_all(action='DESELECT')

        tests.utils.set_active_object(bpy.data.objects['test_verify_uv_1'])
        bpy.ops.io_scene_xray.verify_uv(mode='ACTIVE_OBJECT')
        self.assertEqual(len(bpy.context.selected_objects), 1)

    def test_check_invalid_faces(self):
        # remove default objects
        tests.utils.remove_all_objects()

        # test without selected objects
        bpy.ops.io_scene_xray.check_invalid_faces(
            mode='ACTIVE_OBJECT',
            face_area=True,
            uv_area=True
        )
        self.assertReportsContains(
            'WARNING',
            re.compile('No active object')
        )
        self._reports.clear()

        bpy.ops.io_scene_xray.check_invalid_faces(
            mode='SELECTED_OBJECTS',
            face_area=True,
            uv_area=True
        )
        self.assertReportsContains(
            'WARNING',
            re.compile('No selected objects')
        )
        self._reports.clear()

        bpy.ops.io_scene_xray.check_invalid_faces(
            mode='ALL_OBJECTS',
            face_area=True,
            uv_area=True
        )
        self.assertReportsContains(
            'WARNING',
            re.compile('Current blend-file has no objects')
        )
        self._reports.clear()

        # test selected objects
        verts = [
            # correct face
            [0, 0, 0],
            [1, 0, 0],
            [1, 1, 0],
            [0, 1, 0],
            # invalid face 1
            [0, 0, 0],
            [0.0003, 0, 0],
            [0.0003, 0.0003, 0],
            [0, 0.0003, 0],
            # invalid face 2
            [0, 0, 0],
            [1, 0, 0],
            [0.5, 0, 0]
        ]
        faces = (
            (0, 1, 2),
            (2, 3, 0),
            (4, 5, 6, 7),
            (8, 9, 10)
        )
        uvs = [
            # correct face
            0, 0,
            1, 0,
            1, 1,
            1, 1,
            0, 1,
            0, 0,
            # invalid face 1
            0, 0,
            0.00003, 0,
            0.00003, 0.00003,
            0.00003, 0.00003,
            # invalid face 2
            0, 0,
            0, 0,
            0, 0
        ]

        correct_verts = [
            [0, 0, 0],
            [1, 0, 0],
            [1, 1, 0]
        ]
        correct_faces = [(0, 1, 2), ]
        correct_uvs = [
            0, 0,
            1, 0,
            1, 1
        ]

        for i in range(5):
            mesh = bpy.data.meshes.new('test_invalid_face')
            if i == 3:
                mesh.from_pydata(correct_verts, (), correct_faces)
                uv_coords = correct_uvs
            else:
                mesh.from_pydata(verts, (), faces)
                uv_coords = uvs
            if bpy.app.version >= (2, 80, 0):
                uv_layer = mesh.uv_layers.new(name='uv')
            else:
                uv_tex = mesh.uv_textures.new(name='uv')
                uv_layer = mesh.uv_layers[uv_tex.name]
            uv_layer.data.foreach_set('uv', uv_coords)
            if i == 4:
                obj = bpy.data.objects.new(
                    'test_invalid_face_{}'.format(i),
                    None
                )
            else:
                obj = bpy.data.objects.new(
                    'test_invalid_face_{}'.format(i),
                    mesh
                )
            tests.utils.link_object(obj)
            tests.utils.select_object(obj)

        tests.utils.set_active_object(bpy.data.objects['test_invalid_face_0'])
        bpy.ops.object.mode_set(mode='EDIT')

        bpy.ops.io_scene_xray.check_invalid_faces(
            mode='SELECTED_OBJECTS',
            face_area=True,
            uv_area=True
        )
        self.assertReportsContains(
            'INFO',
            re.compile('Selected objects with invalid faces: 3')
        )
        self._reports.clear()

        bpy.ops.io_scene_xray.check_invalid_faces(
            mode='SELECTED_OBJECTS',
            face_area=True,
            uv_area=False
        )
        self.assertReportsContains(
            'INFO',
            re.compile('Selected objects with invalid faces: 3')
        )
        self._reports.clear()

        bpy.ops.io_scene_xray.check_invalid_faces(
            mode='ALL_OBJECTS',
            face_area=False,
            uv_area=True
        )
        self.assertReportsContains(
            'INFO',
            re.compile('Selected objects with invalid faces: 3')
        )
        self._reports.clear()

    def test_change_fake_user(self):
        for index in range(3):
            name = str(index)
            me = bpy.data.meshes.new(name)
            obj = bpy.data.objects.new(name, me)
            tests.utils.link_object(obj)
            tests.utils.select_object(obj)
            mat = bpy.data.materials.new(name)
            me.materials.append(mat)
            img = bpy.data.images.new(name, 0, 0)
            img.source = 'FILE'
            mat.use_nodes = True
            img_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
            img_node.image = img
            
            arm = bpy.data.armatures.new(name)
            obj = bpy.data.objects.new(name + '_arm', arm)
            tests.utils.link_object(obj)
            tests.utils.select_object(obj)
            act = bpy.data.actions.new(name)
            motion = obj.xray.motions_collection.add()
            motion.name = act.name

        tests.utils.set_active_object(bpy.data.objects[0])

        modes = (
            'ACTIVE_OBJECT',
            'SELECTED_OBJECTS',
            'ALL_OBJECTS',
            'ALL_DATA'
        )
        data = (
            'OBJECTS',
            'MESHES',
            'MATERIALS',
            'TEXTURES',
            'IMAGES',
            'ARMATURES',
            'ACTIONS',
            'ALL'
        )
        fake_users = ('TRUE', 'FALSE', 'INVERT')
        for mode in modes:
            for data_ in data:
                for fake_user in fake_users:
                    bpy.ops.io_scene_xray.change_fake_user(
                        mode=mode,
                        data={data_, },
                        fake_user=fake_user
                    )

    def test_remove_rig(self):
        bpy.ops.object.select_all(action='DESELECT')

        arm = bpy.data.armatures.new('test')
        obj = bpy.data.objects.new('test', arm)

        tests.utils.link_object(obj)
        tests.utils.set_active_object(obj)

        bpy.ops.object.mode_set(mode='EDIT')

        try:
            exp_bone = arm.edit_bones.new('root_bone')
            exp_bone.head = (0, 0, 0)
            exp_bone.tail = (0, 1, 0)

            non_exp_child = arm.edit_bones.new('non_exp_child_bone')
            non_exp_child.head = (2, 0, 0)
            non_exp_child.tail = (0, 3, 0)
            non_exp_child.parent = exp_bone
            non_exp_name = non_exp_child.name

            exp_child = arm.edit_bones.new('exp_child_bone')
            exp_child.head = (2, 0, 2)
            exp_child.tail = (0, 3, 2)
            exp_child.parent = non_exp_child

        finally:
            bpy.ops.object.mode_set(mode='OBJECT')

        arm.bones[non_exp_name].xray.exportable = False

        bpy.ops.object.mode_set(mode='POSE')

        try:
            for bone in obj.pose.bones:
                bone.constraints.new('LIMIT_LOCATION')

        finally:
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.io_scene_xray.remove_rig()

    def test_place_selected_objects(self):
        ver = io_scene_xray.utils.addon_version_number()

        for i in range(5):
            obj = bpy.data.objects.new('test_{}'.format(i), None)
            obj.xray.version = ver
            if i == 3:
                obj.xray.isroot = False
            else:
                obj.xray.isroot = True
            tests.utils.link_object(obj)

        bpy.ops.object.select_all(action='SELECT')

        bpy.ops.io_scene_xray.place_objects(
            plane='XY',
            rows=1,
            offset_h=1.0,
            offset_v=0.5
        )
        bpy.ops.io_scene_xray.place_objects(
            plane='XZ',
            rows=2,
            offset_h=0.2,
            offset_v=1.0
        )
        bpy.ops.io_scene_xray.place_objects(
            plane='YZ',
            rows=3,
            offset_h=2.0,
            offset_v=2.0
        )

    def test_colorize_objects(self):
        # tests without objects
        bpy.ops.io_scene_xray.colorize_objects(
            mode='ACTIVE_OBJECT',
            color_mode='RANDOM_BY_MESH',
            seed=0,
            power=0.5
        )
        bpy.ops.io_scene_xray.colorize_objects(
            mode='SELECTED_OBJECTS',
            color_mode='RANDOM_BY_MESH',
            seed=0,
            power=0.5
        )
        bpy.ops.io_scene_xray.colorize_objects(
            mode='ALL_OBJECTS',
            color_mode='RANDOM_BY_MESH',
            seed=0,
            power=0.5
        )

        for i in range(5):
            if i == 3:
                data = None
            else:
                data = bpy.data.meshes.new('mesh')
            obj = bpy.data.objects.new('test_{}'.format(i), data)
            tests.utils.link_object(obj)
            tests.utils.set_active_object(obj)

        bpy.ops.object.select_all(action='SELECT')

        bpy.ops.io_scene_xray.colorize_objects(
            mode='ACTIVE_OBJECT',
            color_mode='RANDOM_BY_MESH',
            seed=0,
            power=0.5
        )
        bpy.ops.io_scene_xray.colorize_objects(
            mode='SELECTED_OBJECTS',
            color_mode='RANDOM_BY_OBJECT',
            seed=1,
            power=1.0
        )
        bpy.ops.io_scene_xray.colorize_objects(
            mode='ALL_OBJECTS',
            color_mode='RANDOM_BY_ROOT',
            seed=127,
            power=0.0
        )
        bpy.ops.io_scene_xray.colorize_objects(
            mode='ALL_OBJECTS',
            color_mode='SINGLE_COLOR',
            seed=255,
            power=1.0,
            color=(0.8, 0.6, 0.2, 1.0)
        )

    def test_level_shader_nodes(self):
        # create level
        level_obj = bpy.data.objects.new('test_level', None)
        tests.utils.link_object(level_obj)

        xray = level_obj.xray
        lvl = xray.level

        xray.is_level = True
        lvl.object_type = 'LEVEL'

        # create sectors object
        sectors_obj = bpy.data.objects.new('sectors', None)
        sectors_obj.parent = level_obj
        tests.utils.link_object(sectors_obj)
        lvl.sectors_obj = sectors_obj.name

        # create sector objects
        sector_1_obj = bpy.data.objects.new('sector_1', None)
        sector_1_obj.parent = sectors_obj
        tests.utils.link_object(sector_1_obj)

        sector_2_obj = bpy.data.objects.new('sector_2', None)
        sector_2_obj.parent = sectors_obj
        tests.utils.link_object(sector_2_obj)

        # create hierrarhy visual objects
        hier_1_obj = bpy.data.objects.new('hierrarhy_1', None)
        hier_1_obj.parent = sector_1_obj
        hier_1_obj.xray.is_level = True
        hier_1_obj.xray.level.object_type = 'VISUAL'
        hier_1_obj.xray.level.visual_type = 'HIERRARHY'
        tests.utils.link_object(hier_1_obj)

        hier_2_obj = bpy.data.objects.new('hierrarhy_2', None)
        hier_2_obj.parent = sector_2_obj
        hier_2_obj.xray.is_level = True
        hier_2_obj.xray.level.object_type = 'VISUAL'
        hier_2_obj.xray.level.visual_type = 'HIERRARHY'
        tests.utils.link_object(hier_2_obj)

        # create normal visual objects
        norm_1_me = bpy.data.meshes.new('normal')
        norm_1_obj = bpy.data.objects.new('normal', norm_1_me)
        norm_1_obj.parent = hier_1_obj
        norm_1_obj.xray.is_level = True
        norm_1_obj.xray.level.object_type = 'VISUAL'
        norm_1_obj.xray.level.visual_type = 'NORMAL'
        tests.utils.link_object(norm_1_obj)

        norm_2_me = bpy.data.meshes.new('normal')
        norm_2_obj = bpy.data.objects.new('normal', norm_2_me)
        norm_2_obj.parent = hier_2_obj
        norm_2_obj.xray.is_level = True
        norm_2_obj.xray.level.object_type = 'VISUAL'
        norm_2_obj.xray.level.visual_type = 'NORMAL'
        tests.utils.link_object(norm_2_obj)

        # create materials
        bpy.context.scene.render.engine = 'CYCLES'

        # material 1
        mat_1 = bpy.data.materials.new('lmaps')
        mat_1.use_nodes = True
        img_1 = bpy.data.images.new('image_1', 0, 0)
        img_1.source = 'FILE'
        nodes_1 = mat_1.node_tree.nodes
        norm_1_me.materials.append(mat_1)

        lmap_1 = bpy.data.images.new('lmap_1', 0, 0)
        lmap_1.source = 'FILE'

        lmap_2 = bpy.data.images.new('lmap_2', 0, 0)
        lmap_2.source = 'FILE'

        mat_1.xray.lmap_0 = lmap_1.name
        mat_1.xray.lmap_1 = lmap_2.name
        mat_1.xray.hemi_vert_color = 'Hemi'
        mat_1.xray.uv_texture = 'Texture'
        mat_1.xray.uv_light_map = 'Light Map'

        # material 2
        mat_2 = bpy.data.materials.new('lmaps')
        mat_2.use_nodes = True
        img_2 = bpy.data.images.new('image_2', 0, 0)
        img_2.source = 'FILE'
        nodes_2 = mat_2.node_tree.nodes
        norm_2_me.materials.append(mat_2)

        mat_2.xray.light_vert_color = 'Light'
        mat_2.xray.sun_vert_color = 'Sun'
        mat_2.xray.hemi_vert_color = 'Hemi'
        mat_2.xray.uv_texture = 'Texture'

        # create output node
        out_node_1 = nodes_1.new('ShaderNodeOutputMaterial')
        out_node_1.select = False
        out_node_1.location.x = 300
        out_node_1.location.y = 300

        out_node_2 = nodes_2.new('ShaderNodeOutputMaterial')
        out_node_2.select = False
        out_node_2.location.x = 300
        out_node_2.location.y = 300

        # create shader node
        if bpy.app.version >= (2, 79):
            shader_node_1 = nodes_1.new('ShaderNodeBsdfPrincipled')
            color_socket = 'Base Color'
        else:
            shader_node_1 = nodes_1.new('ShaderNodeBsdfDiffuse')
            color_socket = 'Color'
        shader_node_1.select = False
        shader_node_1.location.x = 10
        shader_node_1.location.y = 300

        if bpy.app.version >= (2, 79):
            shader_node_2 = nodes_2.new('ShaderNodeBsdfPrincipled')
        else:
            shader_node_2 = nodes_1.new('ShaderNodeBsdfDiffuse')
        shader_node_2.select = False
        shader_node_2.location.x = 10
        shader_node_2.location.y = 300

        # create image node
        img_node_1 = nodes_1.new('ShaderNodeTexImage')
        img_node_1.image = img_1
        img_node_1.select = False
        img_node_1.location.x = -500
        img_node_1.location.y = 100

        img_node_2 = nodes_2.new('ShaderNodeTexImage')
        img_node_2.image = img_2
        img_node_2.select = False
        img_node_2.location.x = -500
        img_node_2.location.y = 100

        # link nodes
        mat_1.node_tree.links.new(
            shader_node_1.outputs['BSDF'],
            out_node_1.inputs['Surface']
        )
        mat_1.node_tree.links.new(
            img_node_1.outputs['Color'],
            shader_node_1.inputs[color_socket]
        )

        mat_2.node_tree.links.new(
            shader_node_2.outputs['BSDF'],
            out_node_2.inputs['Surface']
        )
        mat_2.node_tree.links.new(
            img_node_2.outputs['Color'],
            shader_node_2.inputs[color_socket]
        )

        # run
        bpy.ops.object.select_all(action='DESELECT')
        tests.utils.select_object(level_obj)
        tests.utils.set_active_object(level_obj)

        bpy.ops.io_scene_xray.create_level_shader_nodes(mode='ACTIVE_LEVEL')
        bpy.ops.io_scene_xray.remove_level_shader_nodes(mode='ACTIVE_LEVEL')

        bpy.ops.io_scene_xray.create_level_shader_nodes(mode='SELECTED_LEVELS')
        bpy.ops.io_scene_xray.remove_level_shader_nodes(mode='SELECTED_LEVELS')

        bpy.ops.io_scene_xray.create_level_shader_nodes(mode='ALL_LEVELS')
        bpy.ops.io_scene_xray.remove_level_shader_nodes(mode='ALL_LEVELS')

        bpy.ops.object.select_all(action='SELECT')
        tests.utils.set_active_object(norm_1_obj)

        bpy.ops.io_scene_xray.create_level_shader_nodes(mode='ACTIVE_OBJECT')
        bpy.ops.io_scene_xray.remove_level_shader_nodes(mode='ACTIVE_OBJECT')

        bpy.ops.io_scene_xray.create_level_shader_nodes(mode='SELECTED_OBJECTS')
        bpy.ops.io_scene_xray.remove_level_shader_nodes(mode='SELECTED_OBJECTS')

        bpy.ops.io_scene_xray.create_level_shader_nodes(mode='ALL_OBJECTS')
        bpy.ops.io_scene_xray.remove_level_shader_nodes(mode='ALL_OBJECTS')

        bpy.ops.io_scene_xray.create_level_shader_nodes(mode='ACTIVE_MATERIAL')
        bpy.ops.io_scene_xray.remove_level_shader_nodes(mode='ACTIVE_MATERIAL')

        bpy.ops.io_scene_xray.create_level_shader_nodes(mode='ALL_MATERIALS', light_format='SOC')
        bpy.ops.io_scene_xray.remove_level_shader_nodes(mode='ALL_MATERIALS')

        bpy.ops.io_scene_xray.create_level_shader_nodes(mode='ALL_MATERIALS', light_format='CSCOP')
        bpy.ops.io_scene_xray.remove_level_shader_nodes(mode='ALL_MATERIALS')

        bpy.ops.io_scene_xray.create_level_shader_nodes(mode='ALL_MATERIALS', light_format='1964-3120')
        bpy.ops.io_scene_xray.remove_level_shader_nodes(mode='ALL_MATERIALS')

        bpy.ops.io_scene_xray.create_level_shader_nodes(mode='ALL_MATERIALS', light_format='3436-3844')
        bpy.ops.io_scene_xray.remove_level_shader_nodes(mode='ALL_MATERIALS')

    def test_set_export_path(self):
        ver = io_scene_xray.utils.addon_version_number()

        obj_1 = bpy.data.objects.new('object_1', None)
        tests.utils.link_object(obj_1)
        obj_1.xray.version = ver
        obj_1.xray.isroot = True

        obj_2 = bpy.data.objects.new('object_2', None)
        tests.utils.link_object(obj_2)
        obj_2.xray.version = ver
        obj_2.xray.isroot = True

        obj_3 = bpy.data.objects.new('object_3', None)
        tests.utils.link_object(obj_3)
        obj_3.xray.version = ver
        obj_3.xray.isroot = True

        prefs = tests.utils.get_preferences()
        prefs.objects_folder = self.outpath(os.path.join('rawdata', 'objects'))
        prefs.meshes_folder = self.outpath(os.path.join('gamedata', 'meshes'))

        bpy.ops.object.select_all(action='DESELECT')
        tests.utils.set_active_object(obj_1)

        exp_path = os.path.join('test', 'folder') + os.sep
        rel_exp_path = exp_path.replace('/', '\\')

        # active object
        bpy.ops.io_scene_xray.set_export_path(
            directory=os.path.join(prefs.objects_folder, exp_path),
            mode='ACTIVE_OBJECT'
        )

        self.assertEqual(obj_1.xray.export_path, rel_exp_path)
        self.assertEqual(obj_2.xray.export_path, '')
        self.assertEqual(obj_3.xray.export_path, '')

        # selected objects
        prefs.objects_folder = self.outpath(os.path.join('rawdata', 'objects')) + os.sep
        prefs.meshes_folder = self.outpath(os.path.join('gamedata', 'meshes')) + os.sep

        for ob in (obj_1, obj_2, obj_3):
            ob.xray.export_path = ''

        tests.utils.select_object(obj_1)
        tests.utils.select_object(obj_2)

        bpy.ops.io_scene_xray.set_export_path(
            directory=os.path.join(prefs.objects_folder, exp_path),
            mode='SELECTED_OBJECTS'
        )

        self.assertEqual(obj_1.xray.export_path, rel_exp_path)
        self.assertEqual(obj_2.xray.export_path, rel_exp_path)
        self.assertEqual(obj_3.xray.export_path, '')

        # all objects
        exp_path = os.path.join('test', 'folder')
        rel_exp_path = exp_path.replace('/', '\\') + '\\'

        bpy.ops.object.select_all(action='DESELECT')

        for ob in (obj_1, obj_2, obj_3):
            ob.xray.export_path = ''

        bpy.ops.io_scene_xray.set_export_path(
            directory=os.path.join(prefs.meshes_folder, exp_path),
            mode='ALL_OBJECTS'
        )

        self.assertEqual(obj_1.xray.export_path, rel_exp_path)
        self.assertEqual(obj_2.xray.export_path, rel_exp_path)
        self.assertEqual(obj_3.xray.export_path, rel_exp_path)

        # no active object
        tests.utils.set_active_object(None)

        bpy.ops.io_scene_xray.set_export_path(
            directory=os.path.join(prefs.objects_folder, exp_path),
            mode='ACTIVE_OBJECT'
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('Root-objects not found')
        )

        # not inside folder
        bpy.ops.io_scene_xray.set_export_path(
            directory='test',
            mode='ALL_OBJECTS'
        )
        self.assertReportsContains(
            'ERROR',
            re.compile('The path is not inside the Meshes or Objects folder')
        )

    def test_change_shader_params(self):
        for i in range(3):
            name = 'test_{}'.format(i)
            mesh = bpy.data.meshes.new(name)
            obj = bpy.data.objects.new(name, mesh)
            mat = bpy.data.materials.new(name)
            if i != 2:
                mat.use_nodes = True
            mesh.materials.append(mat)
            tests.utils.link_object(obj)
            tests.utils.set_active_object(obj)

        # default
        bpy.ops.io_scene_xray.change_shader_params()

        # change all
        if bpy.app.version >= (2, 79, 0):
            bpy.ops.io_scene_xray.change_shader_params(
                mode='ALL_MATERIALS',

                alpha_value=True,
                alpha_change=True,
    
                specular_value=0.1,
                specular_change=True,

                roughness_value=0.1,
                roughness_change=True,

                viewport_roughness_value=0.1,
                viewport_roughness_change=True,

                blend_mode_value='OPAQUE',
                blend_mode_change=True,

                shadow_mode_value='OPAQUE',
                shadow_mode_change=True,

                shader_value='ShaderNodeBsdfPrincipled',
                shader_change=True
            )

            # diffuse
            bpy.ops.io_scene_xray.change_shader_params(
                mode='ALL_MATERIALS',

                alpha_value=True,
                alpha_change=True,
    
                specular_value=0.1,
                specular_change=True,

                roughness_value=0.1,
                roughness_change=True,

                viewport_roughness_value=0.1,
                viewport_roughness_change=True,

                blend_mode_value='OPAQUE',
                blend_mode_change=True,

                shadow_mode_value='OPAQUE',
                shadow_mode_change=True,

                shader_value='ShaderNodeBsdfDiffuse',
                shader_change=True
            )

            # not change
            bpy.ops.io_scene_xray.change_shader_params(
                mode='ALL_MATERIALS',

                alpha_value=True,
                alpha_change=False,
    
                specular_value=0.1,
                specular_change=False,

                roughness_value=0.1,
                roughness_change=False,

                viewport_roughness_value=0.1,
                viewport_roughness_change=False,

                blend_mode_value='OPAQUE',
                blend_mode_change=False,

                shadow_mode_value='OPAQUE',
                shadow_mode_change=False,

                shader_value='ShaderNodeBsdfPrincipled',
                shader_change=False
            )

        if bpy.app.version < (2, 80, 0):
            bpy.context.scene.render.engine = 'BLENDER_RENDER'

            bpy.ops.io_scene_xray.change_shader_params(
                mode='ALL_MATERIALS',

                shadeless_value=True,
                shadeless_change=True,
    
                diffuse_intensity_value =0.1,
                diffuse_intensity_change=True,

                specular_intensity_value=0.1,
                specular_intensity_change=True,

                specular_hardness_value=10,
                specular_hardness_change=True,

                use_transparency_value=True,
                use_transparency_change=True,

                transparency_alpha_value=0.1,
                transparency_alpha_change=True
            )

            bpy.ops.io_scene_xray.change_shader_params(
                mode='ALL_MATERIALS',

                shadeless_value=True,
                shadeless_change=False,
    
                diffuse_intensity_value =0.1,
                diffuse_intensity_change=False,

                specular_intensity_value=0.1,
                specular_intensity_change=False,

                specular_hardness_value=10,
                specular_hardness_change=False,

                use_transparency_value=True,
                use_transparency_change=False,

                transparency_alpha_value=0.1,
                transparency_alpha_change=False
            )
