from tests import utils

import bpy
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
        self._create_objects()

        # Act
        bpy.ops.export_object.xray_objects(
            objects='tobj1,tobj2', directory=self.outpath(),
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
            re.compile('bone .* edited with .* version of this plugin')
        )

    def _create_objects(self):
        bmesh = utils.create_bmesh((
            (0, 0, 0),
            (-1, -1, 0), (+1, -1, 0), (+1, +1, 0), (-1, +1, 0),
        ), ((0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)))

        objs = []
        for i in range(3):
            obj = utils.create_object(bmesh)
            obj.name = 'tobj%d' % (i + 1)
            objs.append(obj)
        objs[1].xray.export_path = 'a/b'
        return objs
