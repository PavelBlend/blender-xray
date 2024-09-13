# standart modules
import os
import shutil
import unittest
import inspect

# blender modules
import bpy
import bmesh
import addon_utils
import mathutils

# addon modules
import io_scene_xray
from io_scene_xray.utils.ie import BaseOperator as TestReadyOperator


class XRayTestCase(unittest.TestCase):
    blend_file = None
    __tests_out = os.path.abspath('.tests')
    _reports = []

    @classmethod
    def relpath(cls, path=None):
        result = os.path.dirname(inspect.getfile(cls))
        if path is not None:
            result = os.path.join(result, path)
        return result

    def outpath(self, path='', mkdirs=True):
        base = os.path.join(
            self.__tests_out,
            self.__class__.__name__,
            self._testMethodName,
        )
        if mkdirs:
            os.makedirs(base, exist_ok=True)
        return os.path.join(base, path)

    @classmethod
    def binpath(cls, path=None):
        result = os.path.dirname(os.path.dirname(inspect.getfile(cls)))
        result = os.path.join(result, 'tested')
        if path is not None:
            result = os.path.join(result, path)
        return result

    def setUp(self):
        opath = self.outpath(mkdirs=False)
        if os.path.exists(opath):
            shutil.rmtree(opath)
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

        addon_utils.disable('io_scene_xray')

    def run(self, result=None):
        def errcount():
            return len(result.errors) + len(result.failures)
    
        count_before = errcount()
        super().run(result)

        if errcount() > count_before:
            bpy.ops.wm.save_mainfile(
                filepath=self.outpath('result.blend')
            )

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
        tmp = self.outpath(mkdirs=False)

        normalized = {
            path.replace('/', os.path.sep)
            for path in expected
        }
        for path in normalized:
            self.assertFileExists(os.path.join(tmp, path))

        def scan_dir(files, path):
            for p in os.listdir(path):
                pp = os.path.join(path, p)
                if os.path.isdir(pp):
                    scan_dir(files, pp)
                else:
                    files.add(pp[len(tmp):])

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
        full_path = self.outpath(file_path, mkdirs=False)
        with open(full_path, 'rb') as file:
            return file.read().replace(b'\x00', b'')

    def _findReport(self, report_type=None, re_message=None):
        for report in self._reports:

            if (report_type is not None) and (report_type not in report[0]):
                continue

            if re_message is None:
                return report

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

    def assertAlmostEqualV(self, first, second, delta, msg=None):
        class V:
            def __init__(self, v):
                self.vec = mathutils.Vector(v)
            def __sub__(self, right):
                return (self.vec - right.vec).length
            def __repr__(self):
                return 'V' + repr(self.vec.to_tuple())

        return self.assertAlmostEqual(V(first), V(second), msg=msg, delta=delta)

    def getFullLogAsText(self):
        return bpy.data.texts['xray_log'].as_string()


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
