from tests import utils

import bpy


class TestFormatObject(utils.XRayTestCase):
    def test_import_separate_materials_without_slots(self):
        # Arrange
        mat = bpy.data.materials.new('Material')

        # Act & Assert
        self._test_import_separate_materials(mat, None)

    def test_import_separate_materials_with_different_name(self):
        # Arrange
        mat, _, tex = self._get_compatible_material()
        mat.name = 'DifferentName'

        # Act & Assert
        self._test_import_separate_materials(mat, tex)

    def test_import_separate_materials_with_different_flags(self):
        # Arrange
        mat, _, tex = self._get_compatible_material()
        mat.xray.flags = 123

        # Act & Assert
        self._test_import_separate_materials(mat, tex)

    def test_import_separate_materials_with_different_eshader(self):
        # Arrange
        mat, _, tex = self._get_compatible_material()
        mat.xray.eshader = 'different_eshader'

        # Act & Assert
        self._test_import_separate_materials(mat, tex)

    def test_import_separate_materials_with_different_cshader(self):
        # Arrange
        mat, _, tex = self._get_compatible_material()
        mat.xray.cshader = 'different_cshader'

        # Act & Assert
        self._test_import_separate_materials(mat, tex)

    def test_import_separate_materials_with_different_gamemtl(self):
        # Arrange
        mat, _, tex = self._get_compatible_material()
        mat.xray.gamemtl = 'different_gamemtl'

        # Act & Assert
        self._test_import_separate_materials(mat, tex)

    def test_import_separate_materials_with_different_vmap(self):
        # Arrange
        mat, mts, tex = self._get_compatible_material()
        mts.uv_layer = 'DifferentUVLayer'

        # Act & Assert
        self._test_import_separate_materials(mat, tex)

    def test_import_separate_materials_with_incompat_texture(self):
        # Arrange
        mat, _, tex = self._get_compatible_material()
        tex.image.filepath = 'incompatible.dds'

        # Act & Assert
        self._test_import_separate_materials(mat, tex)

    def test_import_separate_materials_with_noimage_texture(self):
        # Arrange
        mat, _, tex = self._get_compatible_material()
        tex.image = None

        # Act & Assert
        self._test_import_separate_materials(mat, tex)

    def _test_import_separate_materials(self, mat, tex):
        # Act
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.object'}],
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        imported_material = bpy.data.objects['Plane'].data.materials[0]
        self.assertNotEqual(imported_material, mat)
        imported_texture = imported_material.texture_slots[0].texture
        self.assertNotEqual(imported_texture, tex)

    def test_import_merge_materials(self):
        # Arrange
        mat, _, tex = self._get_compatible_material()

        # Act
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.object'}],
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        imported_material = bpy.data.objects['Plane'].data.materials[0]
        self.assertEqual(imported_material, mat)
        imported_texture = imported_material.texture_slots[0].texture
        self.assertEqual(imported_texture, tex)

    def _get_compatible_material(self):
        img = bpy.data.images.new('texture', 0, 0)
        img.source = 'FILE'
        img.filepath = 'gamedata/textures/Texture.dds'
        tex = bpy.data.textures.new('Texture', type='IMAGE')
        tex.image = img
        mat = bpy.data.materials.new('Material')
        mts = mat.texture_slots.add()
        mts.texture = tex
        return mat, mts, tex
