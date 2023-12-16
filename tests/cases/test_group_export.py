import os
import bpy
import tests
import io_scene_xray


class TestGroupExport(tests.utils.XRayTestCase):
    def test_group_export(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.join(os.curdir, 'tests', 'tested')

        create_objects()

        # Act
        bpy.ops.xray_export.group(filepath=self.outpath('test_export.group'))

        # Assert
        self.assertReportsNotContains('ERROR')


def create_objects():
    ver = io_scene_xray.utils.addon_version_number()

    me = bpy.data.meshes.new('test')

    obj_1 = bpy.data.objects.new('test_1', me)
    obj_1.xray.version = ver
    obj_1.xray.isroot = True
    obj_1.xray.export_path = ''
    tests.utils.link_object(obj_1)
    tests.utils.select_object(obj_1)

    obj_2 = bpy.data.objects.new('test_2', me)
    obj_2.xray.version = ver
    obj_2.xray.isroot = True
    obj_2.xray.export_path = 'test_folder'
    tests.utils.link_object(obj_2)
    tests.utils.select_object(obj_2)

    obj_3 = bpy.data.objects.new('test_3', me)
    obj_3.xray.version = ver
    obj_3.xray.isroot = True
    obj_3.xray.export_path = 'test_folder\\'
    tests.utils.link_object(obj_3)
    tests.utils.select_object(obj_3)

    obj_4 = bpy.data.objects.new('test_3.001', me)
    obj_4.xray.version = ver
    obj_4.xray.isroot = True
    obj_4.xray.export_path = 'test_folder\\subfolder'
    tests.utils.link_object(obj_4)
    tests.utils.select_object(obj_4)

    obj_5 = bpy.data.objects.new('ob', me)
    obj_5.xray.version = ver
    obj_5.xray.export_path = ''
    obj_5.xray.isroot = False
    tests.utils.link_object(obj_5)
    tests.utils.select_object(obj_5)

    obj_6 = bpy.data.objects.new('test.object', me)
    obj_6.xray.version = ver
    obj_6.xray.isroot = True
    obj_6.xray.export_path = 'test\\folder\\'
    tests.utils.link_object(obj_6)
    tests.utils.select_object(obj_6)

    obj_7 = bpy.data.objects.new('test.abc', me)
    obj_7.xray.version = ver
    obj_7.location = (1.0, 2.0, 3.0)
    obj_7.rotation_euler = (0.1, 0.2, 0.3)
    obj_7.xray.isroot = True
    obj_7.xray.export_path = ''
    tests.utils.link_object(obj_7)
    tests.utils.select_object(obj_7)
