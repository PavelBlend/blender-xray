from tests import utils

import bpy


class TestFormatObject(utils.XRayTestCase):
    def test_import_merge_materials(self):
        # Arrange
        tex = bpy.data.textures.new('Texture', type='IMAGE')
        mat = bpy.data.materials.new('Material')
        mts = mat.texture_slots.add()
        mts.texture = tex
        obj = utils.create_object(utils.create_bmesh((
            (0, 0, 0), (-1, -1, 0), (+1, -1, 0),
        ), ((0, 1, 2),)))
        obj.data.materials.append(mat)

        # Act
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.object'}],
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertNotEquals(bpy.data.objects['Plane'].data.materials[0], mat)
