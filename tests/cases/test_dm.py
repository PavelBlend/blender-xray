from tests import utils

import bpy


class TestDmImport(utils.XRayTestCase):
    def test_default(self):
        # Act
        bpy.ops.xray_import.dm(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.dm'}],
        )

        # Assert
        self.assertReportsNotContains('WARNING')

        obj = bpy.data.objects['test_fmt.dm']
        self.assertEqual(obj.xray.no_waving, False)
        self.assertEqual(obj.xray.min_scale, 0.5)
        self.assertEqual(obj.xray.max_scale, 2.0)

        mat = obj.active_material
        self.assertEqual(mat.name, 'fx\\fx_rainsplash1')
        tex = mat.active_texture
        self.assertEqual(tex.name, 'fx\\fx_rainsplash1')
