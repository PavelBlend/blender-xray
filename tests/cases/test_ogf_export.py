import bpy
import io_scene_xray
import tests


class TestOgfExport(tests.utils.XRayTestCase):
    def test_export_general(self):
        # Arrange
        obj = self._create_object('test_object')

        # Act
        bpy.ops.xray_export.ogf_file(
            filepath=self.outpath('test.ogf'),
            fmt_version='soc',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertOutputFiles({'test.ogf'})

    def _create_object(self, name, export_path=''):
        # create mesh
        bmesh = tests.utils.create_bmesh(
            ((0, 0, 0), (-1, -1, 0), (+1, -1, 0), (+1, +1, 0), (-1, +1, 0)),
            ((0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)),
            True
        )

        # create mesh-object
        obj = tests.utils.create_object(bmesh, True)
        obj.name = name
        obj.xray.export_path = export_path

        # create armature-object
        arm = bpy.data.armatures.new(name)
        arm_obj = bpy.data.objects.new(name + '_arm', arm)
        ver = io_scene_xray.utils.addon_version_number()
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
