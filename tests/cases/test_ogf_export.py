import re
import os
import bpy
import tests
import io_scene_xray


class TestOgfExport(tests.utils.XRayTestCase):
    def test_export_active_object(self):
        # Arrange
        bpy.ops.object.select_all(action='DESELECT')
        self._create_object('test_object')

        # Act
        bpy.ops.xray_export.ogf_file(
            filepath=self.outpath('test.ogf'),
            fmt_version='soc',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertOutputFiles({'test.ogf'})

    def test_export_selected_object(self):
        # Arrange
        bpy.ops.object.select_all(action='DESELECT')
        obj = self._create_object('test_object')

        # test lod export
        obj.xray.lodref = 'test\\lod\\ref'

        tests.utils.select_object(obj)

        # Act
        bpy.ops.xray_export.ogf_file(
            filepath=self.outpath('test.ogf'),
            fmt_version='cscop',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertOutputFiles({'test.ogf'})

    def test_export_batch(self):
        # Arrange
        bpy.ops.object.select_all(action='DESELECT')
        for obj_index in range(3):
            obj = self._create_object('test_object_{}'.format(obj_index))
            tests.utils.select_object(obj)

        # Act
        bpy.ops.xray_export.ogf(
            directory=self.outpath(),
            fmt_version='soc',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertOutputFiles({
            'test_object_0.ogf',
            'test_object_1.ogf',
            'test_object_2.ogf'
        })

    def test_export_batch_export_path(self):
        # Arrange
        bpy.ops.object.select_all(action='DESELECT')
        for obj_index in range(3):
            obj = self._create_object('test_object_{}'.format(obj_index))
            obj.xray.export_path = 'test/folder'
            tests.utils.select_object(obj)

        # Act
        bpy.ops.xray_export.ogf(
            directory=self.outpath(),
            fmt_version='soc',
            texture_name_from_image_path=False,
            use_export_paths=True
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertOutputFiles({
            'test/folder/test_object_0.ogf',
            'test/folder/test_object_1.ogf',
            'test/folder/test_object_2.ogf'
        })

    def test_export_batch_without_object(self):
        bpy.ops.object.select_all(action='DESELECT')
        tests.utils.set_active_object(None)

        # Act
        bpy.ops.xray_export.ogf(
            directory=self.outpath(),
            fmt_version='soc',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertReportsContains(
            'ERROR',
            re.compile('Cannot find root-objects')
        )

    def test_export_without_object(self):
        bpy.ops.object.select_all(action='DESELECT')
        tests.utils.set_active_object(None)

        # Act
        bpy.ops.xray_export.ogf_file(
            filepath=self.outpath('test.ogf'),
            fmt_version='soc',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertReportsContains(
            'ERROR',
            re.compile('Cannot find object root')
        )

    def test_export_without_roots(self):
        # Arrange
        bpy.ops.object.select_all(action='DESELECT')
        obj = self._create_object('test_object')
        obj.xray.isroot = False

        # Act
        bpy.ops.xray_export.ogf_file(
            filepath=self.outpath('test.ogf'),
            fmt_version='cscop',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertReportsContains(
            'ERROR',
            re.compile('Cannot find object root')
        )

    def test_export_two_sided(self):
        # Arrange
        bpy.ops.object.select_all(action='DESELECT')
        obj = self._create_object('test_object', two_sided=True)

        # Act
        bpy.ops.xray_export.ogf_file(
            filepath=self.outpath('test_two_sided.ogf'),
            fmt_version='soc',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertOutputFiles({'test_two_sided.ogf'})

    def test_export_userdata(self):
        # Arrange
        bpy.ops.object.select_all(action='DESELECT')
        obj = self._create_object('test_object')
        obj.xray.userdata = 'test user data'

        # Act
        bpy.ops.xray_export.ogf_file(
            filepath=self.outpath('test_userdata.ogf'),
            fmt_version='soc',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertOutputFiles({'test_userdata.ogf'})

    def test_export_motion_refs(self):
        # Arrange
        bpy.ops.object.select_all(action='DESELECT')
        obj = self._create_object('test_object')

        for i in range(3):
            ref = obj.xray.motionrefs_collection.add()
            ref.name = 'test\\ref_{}'.format(i)

        # Act
        bpy.ops.xray_export.ogf_file(
            filepath=self.outpath('test_motion_refs_soc.ogf'),
            fmt_version='soc',
            texture_name_from_image_path=False
        )
        bpy.ops.xray_export.ogf_file(
            filepath=self.outpath('test_motion_refs_cscop.ogf'),
            fmt_version='cscop',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertOutputFiles({
            'test_motion_refs_soc.ogf',
            'test_motion_refs_cscop.ogf'
        })

    def test_export_motions(self):
        # Arrange
        bpy.ops.object.select_all(action='DESELECT')
        obj = self._create_object('test_object')

        bpy.ops.object.mode_set(mode='POSE')

        bpy.ops.pose.group_add()
        bone_group = obj.pose.bone_groups.active
        bone_group.name = 'default'

        obj.pose.bones['test_bone'].bone_group = bone_group

        bpy.ops.object.mode_set(mode='OBJECT')

        act = bpy.data.actions.new(name='test_action')
        act.use_fake_user = True
        motion = obj.xray.motions_collection.add()
        motion.name = act.name

        for i in range(3):
            loc = act.fcurves.new('pose.bones["test_bone"].location', index=i)
            rot = act.fcurves.new('pose.bones["test_bone"].rotation_euler', index=i)
            for i in range(2):
                loc.keyframe_points.insert(i*5, i*1)
                rot.keyframe_points.insert(i*5, i*0.1)

        # Act
        bpy.ops.xray_export.ogf_file(
            filepath=self.outpath('test_motions.ogf'),
            fmt_version='soc',
            export_motions=True,
            texture_name_from_image_path=False
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertOutputFiles({
            'test_motions.ogf',
        })

    def test_export_multiple_bones(self):
        # Arrange
        bpy.ops.object.select_all(action='DESELECT')
        obj = self._create_object('test_object')

        # create new bones
        arm = obj.data
        bpy.ops.object.mode_set(mode='EDIT')
        parent = arm.edit_bones[0]
        try:
            for i in range(2):
                bone = arm.edit_bones.new('test_bone_{}'.format(i))
                bone.head.z = 1.0 + i
                bone.tail.y = 1.0
                bone.tail.z = 1.0 + i
                bone.parent = parent
                parent = bone
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')

        # Act
        bpy.ops.xray_export.ogf_file(
            filepath=self.outpath('test_multiple_bones.ogf'),
            fmt_version='soc',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertOutputFiles({'test_multiple_bones.ogf'})

    def test_export_two_links(self):
        # Arrange
        bpy.ops.object.select_all(action='DESELECT')
        obj = self._create_object('test_object')

        # create new bone
        arm = obj.data
        bpy.ops.object.mode_set(mode='EDIT')
        parent = arm.edit_bones[0]
        try:
            bone = arm.edit_bones.new('test_child')
            bone.head.z = 1.0
            bone.tail.y = 1.0
            bone.tail.z = 1.0
            bone.parent = parent
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')

        # remove preview vertex groups
        mesh_obj = obj.children[0]

        group = mesh_obj.vertex_groups.clear()

        grp1 = mesh_obj.vertex_groups.new(name='test_bone')
        grp2 = mesh_obj.vertex_groups.new(name='test_child')

        verts_count = len(mesh_obj.data.vertices)
        grp1.add(range(verts_count), 0.5, 'REPLACE')
        grp2.add(range(verts_count), 0.5, 'REPLACE')

        # Act
        bpy.ops.xray_export.ogf_file(
            filepath=self.outpath('test_two_links_soc.ogf'),
            fmt_version='soc',
            texture_name_from_image_path=False
        )
        bpy.ops.xray_export.ogf_file(
            filepath=self.outpath('test_two_links_cscop.ogf'),
            fmt_version='cscop',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertOutputFiles({
            'test_two_links_soc.ogf',
            'test_two_links_cscop.ogf'
        })

    def _create_object(self, name, two_sided=False):
        # create mesh
        bmesh = tests.utils.create_bmesh(
            ((0, 0, 0), (-1, -1, 0), (+1, -1, 0), (+1, +1, 0), (-1, +1, 0)),
            ((0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)),
            True
        )

        ver = io_scene_xray.utils.addon_version_number()

        # create mesh-object
        obj = tests.utils.create_object(bmesh, True)
        obj.xray.version = ver
        obj.xray.isroot = False
        obj.name = name + '_mesh'
        obj.data.materials[0].xray.flags_twosided = two_sided

        # create armature-object
        arm = bpy.data.armatures.new(name)
        arm_obj = bpy.data.objects.new(name, arm)
        arm_obj.xray.version = ver
        arm_obj.xray.isroot = True
        tests.utils.link_object(arm_obj)
        tests.utils.set_active_object(arm_obj)

        # create bone
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            bone = arm.edit_bones.new('test_bone')
            bone.tail.y = 1.0
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')

        # added armature modifier
        arm_mod = obj.modifiers.new(name='Armature', type='ARMATURE')
        arm_mod.object = arm_obj
        obj.parent = arm_obj

        # create bone vertex group
        group = obj.vertex_groups.new(name='test_bone')
        vertices_count = len(obj.data.vertices)
        group.add(range(vertices_count), 1, 'REPLACE')

        return arm_obj
