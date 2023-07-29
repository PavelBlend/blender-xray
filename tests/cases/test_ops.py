import re
import bpy
import tests


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
        self.assertReportsContains('WARNING', re.compile('No active object!'))

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
            re.compile('No active object!')
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
