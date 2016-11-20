import unittest
import addon_utils
import inspect
import os
import shutil
import bpy
from io_scene_xray.plugin import TestReadyOperator


class XRayTestCase(unittest.TestCase):
    blend_file = None
    __tmp = '/tmp/io_scene_xray-tests-out'
    _reports = []

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

    def setUp(self):
        self.__prev_report_catcher = TestReadyOperator.report_catcher
        TestReadyOperator.report_catcher = lambda op, type, message: self._reports.append((type, message))

    def tearDown(self):
        TestReadyOperator.report_catcher = self.__prev_report_catcher
        if os.path.exists(self.__tmp):
            shutil.rmtree(self.__tmp)

    def assertFileExists(self, path, allow_empty=False, msg=None):
        if not os.path.isfile(path):
            self.fail(self._formatMessage(msg, 'file {} is not exists'.format(path)))
        if (not allow_empty) and (os.path.getsize(path) == 0):
            self.fail(self._formatMessage(msg, 'file {} is empty'.format(path)))

    def _findReport(self, type=None, re_message=None):
        for r in self._reports:
            if (type is not None) and (type not in r[0]):
                continue
            if re_message is None:
                continue
            m = re_message.match(r[1])
            if m is not None:
                return m

    def assertReportsContains(self, type=None, re_message=None):
        r = self._findReport(type, re_message)
        if r is not None:
            return r
        raise self.fail('Cannot find report with: type={}, message={} in reports: {}'.format(type, re_message, self._reports))

    def assertReportsNotContains(self, type=None, re_message=None):
        r = self._findReport(type, re_message)
        if r is None:
            return
        raise self.fail('Found report with: type={}, message={}: {}'.format(type, re_message, r))
