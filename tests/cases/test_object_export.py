from tests import utils

import bpy
import io_scene_xray
import re


class TestObjectExport(utils.XRayTestCase):
    def test_export_single(self):
        # Arrange
        self._create_objects()

        # Act
        bpy.ops.xray_export.object(
            object='tobj1', filepath=self.outpath('test.object'),
            texture_name_from_image_path=False
        )

        # Assert
        self.assertOutputFiles({
            'test.object'
        })

    def test_export_multi(self):
        # Arrange
        objs = self._create_objects()
        objs[0].location = (1, 2, 3)

        # Act
        bpy.ops.export_object.xray_objects(
            objects='tobj1,tobj2', directory=self.outpath(),
            fmt_version='cscop',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertOutputFiles({
            'tobj1.object',
            'a/b/tobj2.object'
        })

    def test_export_multi_notusing_paths(self):
        # Arrange
        self._create_objects()

        # Act
        bpy.ops.export_object.xray_objects(
            objects='tobj1,tobj2', directory=self.outpath(),
            use_export_paths=False,
            texture_name_from_image_path=False
        )

        # Assert
        self.assertOutputFiles({
            'tobj1.object',
            'tobj2.object'
        })

    def test_export_project(self):
        # Arrange
        self._create_objects()
        for obj in bpy.data.objects:
            obj.select = obj.name in {'tobj1', 'tobj2'}

        # Act
        bpy.ops.export_scene.xray(
            filepath=self.outpath(),
            use_selection=True
        )
        self.assertOutputFiles({
            'tobj1.object',
            'a/b/tobj2.object'
        })

    def test_obsolete_bones(self):
        # Arrange
        objs = self._create_objects()

        arm = bpy.data.armatures.new('tarm')
        obj = bpy.data.objects.new('tobj', arm)
        bpy.context.scene.objects.link(obj)
        bpy.context.scene.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            bone = arm.edit_bones.new('tbone')
            bone.tail.y = 1
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        arm.bones['tbone'].xray.shape.type = '2'
        arm.bones['tbone'].xray.shape.sph_rad = 1

        objs[0].modifiers.new(name='Armature', type='ARMATURE').object = obj
        objs[0].parent = obj
        grp = objs[0].vertex_groups.new()
        grp.add(range(3), 1, 'REPLACE')
        grp = objs[0].vertex_groups.new(io_scene_xray.utils.BAD_VTX_GROUP_NAME)
        grp.add([3], 1, 'REPLACE')

        # Act
        bpy.ops.export_object.xray_objects(
            objects='tobj', directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False,
        )

        # Assert
        self.assertOutputFiles({
            'tobj.object',
        })
        self.assertReportsContains(
            'WARNING',
            re.compile('Bone edited with a different version of this plugin')
        )

    def test_empty_bone_groups(self):
        # Arrange
        arm = bpy.data.armatures.new('tarm')
        obj = bpy.data.objects.new('tobj', arm)
        bpy.context.scene.objects.link(obj)
        bpy.context.scene.objects.active = obj
        b_exp0, b_non0, b_exp1, b_non1 = (
            'b-exportable0', 'b-non-exportable0', 'b-exportable1', 'b-non-exportable1'
        )
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            for n in (b_exp0, b_non0, b_exp1, b_non1):
                bone = arm.edit_bones.new(n)
                bone.tail.y = 1
        finally:
            bpy.ops.object.mode_set(mode='POSE')
        bg_exp = obj.pose.bone_groups.new(name='bg-only-exportable')
        bg_mix = obj.pose.bone_groups.new(name='bg-mixed')
        bg_non = obj.pose.bone_groups.new(name='bg-only-non-exportable')
        bg_emp = obj.pose.bone_groups.new(name='bg-empty')
        obj.pose.bones[b_exp0].bone_group = bg_exp
        obj.pose.bones[b_non0].bone_group = bg_mix
        obj.pose.bones[b_exp1].bone_group = bg_mix
        obj.pose.bones[b_non0].bone_group = bg_non
        arm.bones[b_non0].xray.exportable = False
        arm.bones[b_non1].xray.exportable = False

        # Act
        bpy.ops.export_object.xray_objects(
            objects='tobj', directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False,
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertOutputFiles({
            'tobj.object',
        })
        content = self.getFileSafeContent('tobj.object')
        self.assertRegex(content, re.compile(bytes(b_exp0, 'cp1251')))
        self.assertRegex(content, re.compile(bytes(b_exp1, 'cp1251')))
        self.assertNotRegex(content, re.compile(bytes(b_non0, 'cp1251')))
        self.assertNotRegex(content, re.compile(bytes(b_non1, 'cp1251')))
        self.assertRegex(content, re.compile(bytes(bg_exp.name, 'cp1251')))
        self.assertRegex(content, re.compile(bytes(bg_mix.name, 'cp1251')))
        self.assertNotRegex(content, re.compile(bytes(bg_non.name, 'cp1251')))
        self.assertNotRegex(content, re.compile(bytes(bg_emp.name, 'cp1251')))

    def test_export_no_uvmap(self):
        # Arrange
        self._create_objects(create_uv=False)

        # Act
        bpy.ops.xray_export.object(
            object='tobj1', filepath=self.outpath('test.object'),
        )

        # Assert
        self.assertReportsContains(
            'WARNING',
            re.compile('UV-map is required, but not found')
        )

    def test_export_no_material(self):
        # Arrange
        self._create_objects(create_material=False)

        # Act
        bpy.ops.xray_export.object(
            object='tobj1', filepath=self.outpath('test.object'),
        )

        # Assert
        self.assertReportsContains(
            'WARNING',
            re.compile('Mesh has no material')
        )

    def test_export_fix_smoothing_groups(self):
        # Arrange
        bmesh = utils.create_bmesh((
            (0, 0, 0), (1, 0, 0),
            (1, 1, 0), (1, 1, 0),
        ), ((0, 1, 2), (1, 0, 3)), True)

        obj = utils.create_object(bmesh, True)

        # Act
        bpy.ops.xray_export.object(
            object=obj.name, filepath=self.outpath('test.object'),
        )

        # Assert
        bpy.ops.xray_import.object(
            directory=self.outpath(),
            files=[{'name': 'test.object'}],
        )
        edges = bpy.data.objects['test.object'].data.edges
        sharp_edges = [e for e in edges if e.use_edge_sharp]
        self.assertEqual(len(sharp_edges), 1)

    def _create_objects(self, create_uv=True, create_material=True):
        bmesh = utils.create_bmesh((
            (0, 0, 0),
            (-1, -1, 0), (+1, -1, 0), (+1, +1, 0), (-1, +1, 0),
        ), ((0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)), create_uv)

        objs = []
        for i in range(3):
            obj = utils.create_object(bmesh, create_material)
            obj.name = 'tobj%d' % (i + 1)
            objs.append(obj)
        objs[1].xray.export_path = 'a/b'
        return objs
