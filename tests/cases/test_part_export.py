import os
import re
import shutil
import bpy
import tests
import io_scene_xray


class TestPartExport(tests.utils.XRayTestCase):
    def test_soc_part_export(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.join(os.curdir, 'tests', 'tested')

        create_objects()

        out_path = self.outpath('test_export_soc.part')
        part_file = os.path.join(self.binpath(), 'test_fmt_soc.part')
        shutil.copyfile(part_file, out_path)

        # Act
        bpy.ops.xray_export.part(filepath=out_path, fmt_ver='soc')

        # Assert
        self.assertReportsNotContains('ERROR')

    def test_cscop_part_export(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.join(os.curdir, 'tests', 'tested')

        create_objects()

        out_path = self.outpath('test_export_cscop.part')
        part_file = os.path.join(self.binpath(), 'test_fmt_cs_cop.part')
        shutil.copyfile(part_file, out_path)

        # Act
        bpy.ops.xray_export.part(filepath=out_path, fmt_ver='cscop')

        # Assert
        self.assertReportsNotContains('ERROR')

    def test_no_file(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.join(os.curdir, 'tests', 'tested')

        create_objects()

        # Act
        bpy.ops.xray_export.part(filepath=self.outpath('test_export.part'))

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('Saving to a new file is not supported. Need to export over existing file.')
        )

    def test_no_guid(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.join(os.curdir, 'tests', 'tested')

        create_objects()

        out_path = self.outpath('test_export.part')
        part_file = os.path.join(self.binpath(), 'test_fmt.object')
        shutil.copyfile(part_file, out_path)

        # Act
        bpy.ops.xray_export.part(filepath=out_path)

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('File has no GUID data')
        )


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
