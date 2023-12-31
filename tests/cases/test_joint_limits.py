import bpy
import tests


class TestJointLimits(tests.utils.XRayTestCase):
    def test_general(self):
        # Create object
        arm_obj, arm = self._create_objects()

        # Init
        ik = arm.bones[0].xray.ikjoint
        ik.type = '5'    # slider

        float_str = lambda value: '{0:.8f}'.format(value)

        # Assert
        ik.slide_min = 0.5
        self.assertEqual(float_str(ik.slide_min), float_str(-0.5))

        ik.slide_max = -0.5
        self.assertEqual(float_str(ik.slide_max), float_str(0.5))

        ik.lim_x_min = 0.1
        self.assertEqual(float_str(ik.lim_x_min), float_str(-0.1))

        ik.lim_x_max = -0.1
        self.assertEqual(float_str(ik.lim_x_max), float_str(0.1))

        # Export *.object
        bpy.ops.xray_export.object_file(
            object=bpy.context.active_object.name,
            filepath=self.outpath('test_joint_limits_1.object'),
            texture_name_from_image_path=False
        )

        # Export *.ogf
        bpy.ops.xray_export.ogf_file(
            filepath=self.outpath('test_joint_limits_1.ogf'),
            fmt_version='soc',
            texture_name_from_image_path=False
        )

        # Import *.object
        bpy.ops.xray_import.object(
            directory=self.outpath(),
            files=[{'name': 'test_joint_limits_1.object'}],
        )

        # Import *.ogf
        bpy.ops.xray_import.ogf(
            directory=self.outpath(),
            files=[{'name': 'test_joint_limits_1.ogf'}],
        )

        self.assertReportsNotContains('ERROR')

        for ext in ('.object', '.ogf'):
            # Init
            imported_object = bpy.data.objects['test_joint_limits_1' + ext]
            imp_ik = imported_object.data.bones[0].xray.ikjoint

            # Assert
            self.assertEqual(imp_ik.type, '5')
            self.assertEqual(float_str(imp_ik.slide_min), float_str(-0.5))
            self.assertEqual(float_str(imp_ik.slide_max), float_str(+0.5))
            self.assertEqual(float_str(imp_ik.lim_x_min), float_str(-0.5))
            self.assertEqual(float_str(imp_ik.lim_x_max), float_str(+0.5))

        # Change settings
        tests.utils.set_active_object(arm_obj)
        arm_obj.data.bones[0].xray.ikjoint.type = '2'    # joint

        # Export *.object
        bpy.ops.xray_export.object_file(
            object=bpy.context.active_object.name,
            filepath=self.outpath('test_joint_limits_2.object'),
            texture_name_from_image_path=False
        )

        # Export *.ogf
        bpy.ops.xray_export.ogf_file(
            filepath=self.outpath('test_joint_limits_2.ogf'),
            fmt_version='soc',
            texture_name_from_image_path=False
        )

        # Import *.object
        bpy.ops.xray_import.object(
            directory=self.outpath(),
            files=[{'name': 'test_joint_limits_2.object'}],
        )

        # Import *.ogf
        bpy.ops.xray_import.ogf(
            directory=self.outpath(),
            files=[{'name': 'test_joint_limits_2.ogf'}],
        )

        self.assertReportsNotContains('ERROR')

        for ext in ('.object', '.ogf'):
            # Init
            imported_object = bpy.data.objects['test_joint_limits_2' + ext]
            imp_ik = imported_object.data.bones[0].xray.ikjoint

            # Assert
            self.assertEqual(imp_ik.type, '2')
            self.assertEqual(float_str(imp_ik.slide_min), float_str(-0.1))
            self.assertEqual(float_str(imp_ik.slide_max), float_str(+0.1))
            self.assertEqual(float_str(imp_ik.lim_x_min), float_str(-0.1))
            self.assertEqual(float_str(imp_ik.lim_x_max), float_str(+0.1))

    def _create_objects(self):
        tests.utils.remove_all_objects()

        # create armature
        arm = bpy.data.armatures.new('test_joint_limits')
        arm_obj = bpy.data.objects.new('test_joint_limits', arm)
        tests.utils.link_object(arm_obj)
        tests.utils.set_active_object(arm_obj)

        # create bone
        try:
            bpy.ops.object.mode_set(mode='EDIT')
            bone = arm.edit_bones.new(name='bone')
            bone.head = (0.0, 0.0, 0.0)
            bone.tail = (0.0, 0.0, 1.0)

        finally:
            bpy.ops.object.mode_set(mode='OBJECT')

        # set active bone
        arm.bones.active = arm.bones[0]

        # create mesh
        mesh = bpy.data.meshes.new('test_joint_limits_mesh')
        mesh_obj = bpy.data.objects.new('test_joint_limits_mesh', mesh)
        tests.utils.link_object(mesh_obj)
        tests.utils.set_active_object(mesh_obj)
        mesh_obj.parent = arm_obj

        # create material
        bpy.context.scene.render.engine = 'CYCLES'
        mat = bpy.data.materials.new('material')
        mesh.materials.append(mat)
        mat.use_nodes = True

        # create image
        img = bpy.data.images.new('test\\test_texture', 0, 0)

        if bpy.app.version >= (2, 80, 0):
            img_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
            img_node.name = 'test\\test_texture'
            img_node.label = 'test\\test_texture'
            img_node.image = img
            mat.node_tree.nodes.active = img_node
        else:
            tex = bpy.data.textures.new('test\\test_texture', 'IMAGE')
            tex_slot = mat.texture_slots.add()
            tex_slot.texture = tex
            tex.image = img

        # create geometry
        try:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.primitive_cube_add()

            bpy.ops.object.mode_set(mode='OBJECT')

            for edge in mesh.edges:
                edge.use_seam = True

            bpy.ops.object.mode_set(mode='EDIT')

            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.unwrap()

        finally:
            bpy.ops.object.mode_set(mode='OBJECT')

        # create vertex group
        group = mesh_obj.vertex_groups.new(name=arm.bones.active.name)
        group.add(list(range(len(mesh.vertices))), 1.0, 'REPLACE')

        # create armature modifier
        arm_mod = mesh_obj.modifiers.new('Armature', 'ARMATURE')
        arm_mod.object = arm_obj

        # set active armature object
        tests.utils.set_active_object(arm_obj)
        arm_obj.xray.isroot = True
        arm.xray.joint_limits_type = 'XRAY'

        return arm_obj, arm
