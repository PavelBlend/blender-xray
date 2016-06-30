import unittest
import addon_utils
import inspect
import os
import bpy


class XRayTestCase(unittest.TestCase):
    blend_file = None
    __tmp = '/tmp/io_scene_xray-tests-out'

    @classmethod
    def setUpClass(cls):
        addon_utils.enable('io_scene_xray', default_set=True)
        if cls.blend_file:
            bpy.ops.wm.open_mainfile(filepath=cls.relpath(cls.blend_file))

    @classmethod
    def tearDownClass(cls):
        addon_utils.disable('io_scene_xray')

    @classmethod
    def relpath(cls, path):
        return os.path.join(os.path.dirname(inspect.getfile(cls)), path)

    @classmethod
    def outpath(cls, path=''):
        if not os.path.exists(cls.__tmp):
            os.mkdir(cls.__tmp)
        return os.path.join(cls.__tmp, path)

    def tearDown(self):
        if os.path.exists(self.__tmp):
            for e in os.listdir(self.__tmp):
                os.remove(os.path.join(self.__tmp, e))

    def assertFileExists(self, path, allow_empty=False, msg=None):
        if not os.path.isfile(path):
            self.fail(self._formatMessage(msg, 'file {} is not exists'.format(path)))
        if (not allow_empty) and (os.path.getsize(path) == 0):
            self.fail(self._formatMessage(msg, 'file {} is empty'.format(path)))
