# standart modules
import os
import sys
import shutil
import unittest
import inspect
import tempfile

# blender modules
import bpy
import bmesh
import addon_utils

# addon modules
import io_scene_xray
from io_scene_xray.utils.ie import BaseOperator as TestReadyOperator


class XRayTestCase(unittest.TestCase):
    blend_file = None
    __save_test_data = '--save-test-data' in sys.argv
    __tmp_base = os.path.join(tempfile.gettempdir(), 'io_scene_xray-tests')
    __tmp = os.path.join(__tmp_base, 'out')
    _reports = []

    @classmethod
    def relpath(cls, path=None):
        result = os.path.dirname(inspect.getfile(cls))
        if path is not None:
            result = os.path.join(result, path)
        return result

    @classmethod
    def outpath(cls, path=''):
        if not os.path.exists(cls.__tmp):
            os.makedirs(cls.__tmp)
        return os.path.join(cls.__tmp, path)

    @classmethod
    def binpath(cls, path=None):
        result = os.path.dirname(os.path.dirname(inspect.getfile(cls)))
        result = os.path.join(result, 'tested')
        if path is not None:
            result = os.path.join(result, path)
        return result

    def setUp(self):
        self._reports = []
        if self.blend_file:
            bpy.ops.wm.open_mainfile(filepath=self.relpath(self.blend_file))
        else:
            bpy.ops.wm.read_homefile()
        addon_utils.enable('io_scene_xray', default_set=True)
        io_scene_xray.handlers.load_post(None)
        self.__prev_report_catcher = TestReadyOperator.report_catcher
        TestReadyOperator.report_catcher = lambda op, report_type, message: self._reports.append((report_type, message))
        # Enable scripts so that there are no warnings
        # in the console about disabled drivers.
        if bpy.app.version >= (2, 80, 0):
            bpy.context.preferences.filepaths.use_scripts_auto_execute = True
        else:
            bpy.context.user_preferences.system.use_scripts_auto_execute = True

    def tearDown(self):
        TestReadyOperator.report_catcher = self.__prev_report_catcher
        if os.path.exists(self.__tmp):
            if self.__save_test_data:
                bpy.ops.wm.save_mainfile(
                    filepath=os.path.join(self.__tmp, 'result.blend')
                )
                new_path = os.path.join(
                    self.__tmp_base,
                    self.__class__.__name__,
                    self._testMethodName
                )
                os.renames(self.__tmp, new_path)
            else:
                shutil.rmtree(self.__tmp)
        addon_utils.disable('io_scene_xray')

    def assertFileExists(self, path, allow_empty=False, msg=None):
        if not os.path.isfile(path):
            self.fail(self._formatMessage(
                msg,
                'file {} is not exists'.format(path)
            ))

        if (not allow_empty) and (os.path.getsize(path) == 0):
            self.fail(self._formatMessage(
                msg,
                'file {} is empty'.format(path)
            ))

    def assertOutputFiles(self, expected):
        tmp = self.__tmp

        normalized = {
            path.replace('/', os.path.sep)
            for path in expected
        }
        for path in normalized:
            self.assertFileExists(os.path.join(tmp, path))

        def scan_dir(files, path=''):
            for p in os.listdir(path):
                pp = os.path.join(path, p)
                if os.path.isdir(pp):
                    scan_dir(files, pp)
                else:
                    files.add(pp[len(tmp) + 1:])

        existing = set()
        scan_dir(existing, tmp)
        orphaned = existing - normalized
        if orphaned:
            self.fail(self._formatMessage(
                None,
                'files {} orphaned'.format(orphaned)
            ))

    def assertFileContains(self, file_path, re_message=None):
        content = self.getFileSafeContent(file_path)
        match = re_message.match(content)
        if match is not None:
            raise self.fail(
                'Cannot match the "{}" file content with "{}"'.format(
                    file_path,
                    re_message
                ))

    def getFileSafeContent(self, file_path):
        full_path = os.path.join(self.__tmp, file_path)
        with open(full_path, 'rb') as file:
            return file.read().replace(b'\x00', b'')

    def _findReport(self, report_type=None, re_message=None):
        for report in self._reports:
            if (report_type is not None) and (report_type not in report[0]):
                continue
            if re_message is None:
                continue
            match = re_message.match(report[1])
            if match is not None:
                return match

    def assertReportsContains(self, report_type=None, re_message=None):
        report = self._findReport(report_type, re_message)
        if report is not None:
            return report
        raise self.fail('Cannot find report with: type={}, message={} in reports: {}'.format(
            report_type,
            re_message,
            self._reports
        ))

    def assertReportsNotContains(self, report_type=None, re_message=None):
        report = self._findReport(report_type, re_message)
        if report is None:
            return
        raise self.fail('Found report with: type={}, message={}: {}'.format(
            report_type,
            re_message,
            report
        ))

    def getFullLogAsText(self):
        return bpy.data.texts[-1].as_string()


def create_bmesh(verts, faces, create_uv=True):
    bm = bmesh.new()

    verts = [bm.verts.new(coord) for coord in verts]

    for indices in faces:
        bm.faces.new((verts[vert_index] for vert_index in indices))

    if create_uv:
        bm.loops.layers.uv.new('uv')

    return bm


def link_object(obj):
    if bpy.app.version >= (2, 80, 0):
        bpy.context.scene.collection.objects.link(obj)
    else:
        bpy.context.scene.objects.link(obj)


def select_object(obj):
    if bpy.app.version >= (2, 80, 0):
        obj.select_set(True)
    else:
        obj.select = True


def set_active_object(obj):
    if bpy.app.version >= (2, 80, 0):
        bpy.context.view_layer.objects.active = obj
    else:
        bpy.context.scene.objects.active = obj


def remove_object(obj):
    if bpy.app.version < (2, 80, 0):
        bpy.context.scene.objects.unlink(obj)
    bpy.data.objects.remove(obj)


def remove_all_objects():
    for obj in bpy.data.objects:
        remove_object(obj)


def create_object(bm, create_material=True):
    mesh = bpy.data.meshes.new('test')
    bm.to_mesh(mesh)
    if create_material:
        mat = bpy.data.materials.new('mat')
        mat.use_nodes = True
        mesh.materials.append(mat)
        prefs = get_preferences()
        prefs.textures_folder = 'gamedata\\textures'
        bpy_image = bpy.data.images.new('test_image', 0, 0)
        bpy_image.source = 'FILE'
        bpy_image.filepath = os.path.abspath(os.path.join(
            prefs.textures_folder_auto,
            'test_image'
        ))
        if bpy.app.version >= (2, 80, 0):
            img_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
            img_node.image = bpy_image
        else:
            bpy_texture = bpy.data.textures.new('test_texture', 'IMAGE')
            bpy_texture.image = bpy_image
            tex_slot = mat.texture_slots.add()
            tex_slot.texture = bpy_texture
    obj = bpy.data.objects.new('test', mesh)
    link_object(obj)
    return obj


def get_preferences():
    if bpy.app.version >= (2, 80, 0):
        pref = bpy.context.preferences
    else:
        pref = bpy.context.user_preferences
    return pref.addons['io_scene_xray'].preferences
