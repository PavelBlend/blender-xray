import unittest
import addon_utils
import inspect
import os
import bpy
from io_scene_xray.plugin import TestReadyOperator


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
    def relpath(cls, path=None):
        result = os.path.dirname(inspect.getfile(cls))
        if path is not None:
            result = os.path.join(result, path)
        return result

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


class OpReportCatcher:
    _reports = []

    def __enter__(self):
        self._prev = TestReadyOperator.report_catcher
        TestReadyOperator.report_catcher = lambda op, type, message: self._reports.append((type, message))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        TestReadyOperator.report_catcher = self._prev

    def assertContains(self, type=None, re_message=None):
        for r in self._reports:
            if (type is not None) and (type not in r[0]):
                continue
            if re_message is None:
                continue
            m = re_message.match(r[1])
            if m is not None:
                return m.group(1)
        raise AssertionError('Cannot find report with: type={}, message={}'.format(type, re_message))
