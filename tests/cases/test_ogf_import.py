from tests import utils

import re
import bpy


class TestOgfImport(utils.XRayTestCase):
    def test_import_general(self):
        bpy.ops.xray_import.ogf(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_ogf_st.ogf'}],
        )
        bpy.ops.xray_import.ogf(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_ogf_pm_1_link.ogf'}],
        )
        bpy.ops.xray_import.ogf(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_ogf_pm_act.ogf'}],
        )
        bpy.ops.xray_import.ogf(
            directory=self.binpath(),
            files=[
                {'name': 'test_fmt_ogf_pm_act.ogf'},
                {'name': 'test_fmt_ogf_pm_1_link.ogf'},
                {'name': 'test_fmt_ogf_st.ogf'}
            ],
        )
        bpy.ops.xray_import.ogf(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_ogf_v3.ogf'}],
        )

    def test_import_gunslinger(self):
        bpy.ops.xray_import.ogf(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_ogf_gl.ogf'}],
        )
        self.assertReportsContains(
            'WARNING',
            re.compile('Description isn\'t properly read')
        )
