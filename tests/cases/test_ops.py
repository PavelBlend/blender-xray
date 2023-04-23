import bpy

from tests import utils


class TestOps(utils.XRayTestCase):
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

    def test_copy_paste_action_settings(self):
        # copy
        act = bpy.data.actions.new('test_act_copy')
        arm = bpy.data.armatures.new('test_arm_copy')
        obj = bpy.data.objects.new('test_obj_copy', arm)
        obj.animation_data_create().action = act
        utils.link_object(obj)
        utils.select_object(obj)
        utils.set_active_object(obj)
        bpy.ops.io_scene_xray.copy_action_settings()

        # paste
        act = bpy.data.actions.new('test_act_paste')
        arm = bpy.data.armatures.new('test_arm_paste')
        obj = bpy.data.objects.new('test_obj_paste', arm)
        obj.animation_data_create().action = act
        utils.link_object(obj)
        utils.select_object(obj)
        utils.set_active_object(obj)
        bpy.ops.io_scene_xray.paste_action_settings()

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
            uv_layer.data.foreach_set('uv', uvs)
            obj = bpy.data.objects.new('test_verify_uv', mesh)
            utils.link_object(obj)
            utils.select_object(obj)
            for vert in verts:
                vert[0] += 2
            uv_offset_x, uv_offset_y = uv_offsets[i]
            for uv_index in range(0, len(uvs), 2):
                uvs[uv_index] += uv_offset_x
                uvs[uv_index + 1] += uv_offset_y
        obj = bpy.data.objects.new('test_verify_uv_empty', None)
        utils.link_object(obj)
        utils.select_object(obj)
        bpy.ops.io_scene_xray.verify_uv()

        self.assertEqual(len(bpy.context.selected_objects), 1)

    def test_change_fake_user(self):
        for index in range(3):
            name = str(index)
            me = bpy.data.meshes.new(name)
            obj = bpy.data.objects.new(name, me)
            utils.link_object(obj)
            utils.select_object(obj)
            mat = bpy.data.materials.new(name)
            me.materials.append(mat)
            img = bpy.data.images.new(name, 0, 0)
            img.source = 'FILE'
            mat.use_nodes = True
            img_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
            img_node.image = img
            
            arm = bpy.data.armatures.new(name)
            obj = bpy.data.objects.new(name + '_arm', arm)
            utils.link_object(obj)
            utils.select_object(obj)
            act = bpy.data.actions.new(name)
            motion = obj.xray.motions_collection.add()
            motion.name = act.name

        utils.set_active_object(bpy.data.objects[0])

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
