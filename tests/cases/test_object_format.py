from tests import utils

import bpy
import re


class TestFormatObject(utils.XRayTestCase):
    def test_import_sg_maya(self):
        # Act
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_sg_maya.object'}],
        )

        # Assert
        data = bpy.data.meshes[-1]
        self.assertEqual(len(data.edges), 6)
        self.assertEqual(len([e for e in data.edges if e.use_edge_sharp]), 5)

    def test_import_sg_new(self):
        # Act
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            fmt_version='cscop',
            files=[{'name': 'test_fmt_sg_new.object'}],
        )

        # Assert
        data = bpy.data.meshes[-1]
        self.assertEqual(len(data.edges), 6)
        self.assertEqual(len([e for e in data.edges if e.use_edge_sharp]), 5)

    def test_import_merge_materials_texture_case(self):
        # Arrange
        original_materials_count = len(bpy.data.materials)

        # Act
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_texture_caps.object'}],
        )
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_texture_caps.object'}],
        )

        # Assert
        self.assertEqual(len(bpy.data.materials), original_materials_count + 1)

    def test_import_with_empty_polygons(self):
        # Act
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_invalid_face.object'}],
        )

        # Assert
        self.assertReportsContains('WARNING', re.compile('Invalid face found'))

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
        self._test_import_separate_materials(mat, tex, tex_equal=True)

    def test_import_separate_materials_with_different_flags(self):
        # Arrange
        mat, _, tex = self._get_compatible_material()
        mat.xray.flags = 123

        # Act & Assert
        self._test_import_separate_materials(mat, tex, tex_equal=True)

    def test_import_separate_materials_with_different_eshader(self):
        # Arrange
        mat, _, tex = self._get_compatible_material()
        mat.xray.eshader = 'different_eshader'

        # Act & Assert
        self._test_import_separate_materials(mat, tex, tex_equal=True)

    def test_import_separate_materials_with_different_cshader(self):
        # Arrange
        mat, _, tex = self._get_compatible_material()
        mat.xray.cshader = 'different_cshader'

        # Act & Assert
        self._test_import_separate_materials(mat, tex, tex_equal=True)

    def test_import_separate_materials_with_different_gamemtl(self):
        # Arrange
        mat, _, tex = self._get_compatible_material()
        mat.xray.gamemtl = 'different_gamemtl'

        # Act & Assert
        self._test_import_separate_materials(mat, tex, tex_equal=True)

    def test_import_separate_materials_with_different_vmap(self):
        # Arrange
        mat, mts, tex = self._get_compatible_material()
        if not bpy.app.version >= (2, 80, 0):
            mts.uv_layer = 'DifferentUVLayer'

            # Act & Assert
            self._test_import_separate_materials(mat, tex, tex_equal=True)

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

    def _test_import_separate_materials(self, mat, tex, tex_equal=False):
        # Act
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt.object'}],
        )

        # Assert
        self.assertReportsNotContains('ERROR')
        imported_object = bpy.data.objects['test_fmt.object']
        self.assertEqual(imported_object.data.name, 'plobj')
        imported_material = imported_object.data.materials[0]
        self.assertNotEqual(imported_material, mat)
        if not bpy.app.version >= (2, 80, 0):
            imported_texture = imported_material.texture_slots[0].texture
            if tex_equal:
                self.assertEqual(imported_texture, tex)
            else:
                self.assertNotEqual(imported_texture, tex)

    def test_import_merge_materials(self):
        # Arrange
        mat, _, tex = self._get_compatible_material()
        prefs = utils.get_preferences()
        tex_folder = prefs.textures_folder
        prefs.textures_folder = 'gamedata/textures/'

        # Act
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt.object'}],
        )

        prefs.textures_folder = tex_folder

        # Assert
        self.assertReportsNotContains('WARNING')
        imported_material = bpy.data.objects['test_fmt.object'].data.materials[0]
        self.assertEqual(imported_material, mat)
        if not bpy.app.version >= (2, 80, 0):
            imported_texture = imported_material.texture_slots[0].texture
            self.assertEqual(imported_texture, tex)

    def test_export_single_mesh(self):
        # Arrange
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt.object'}],
        )

        obj = bpy.data.objects[-1]
        obj.name = 'uniq-obj-name'
        obj.data.name = 'uniq-msh-name'

        # Act
        bpy.ops.xray_export.object(
            objects=obj.name, directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False,
        )

        # Assert
        self.assertFileContains('uniq-obj-name.object', re.compile(b'uniq-msh-name'))

    def test_import_no_texture(self):
        # Arrange
        mat = _create_compatible_material_object()

        # Act
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_no_texture.object'}],
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        imported_material = bpy.data.objects['test_fmt_no_texture.object'].data.materials[0]
        self.assertEqual(imported_material, mat)
        if not bpy.app.version >= (2, 80, 0):
            all_slots_are_empty = all(not slot for slot in imported_material.texture_slots)
            self.assertTrue(all_slots_are_empty)

    def test_import_old_format(self):
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_old.object'}],
        )

        # Assert
        self.assertReportsNotContains('ERROR')

        obj = bpy.data.objects['test_fmt_old.object']
        material = obj.data.materials[0]
        self.assertEqual(obj.data.name, 'Plane01')
        self.assertEqual(material.name, '1 - Defaultsa')
        self.assertEqual(material.xray.eshader, 'details\set')
        self.assertEqual(material.xray.cshader, 'default')
        self.assertEqual(material.xray.gamemtl, 'default')
        if not bpy.app.version >= (2, 80, 0):
            texture = material.texture_slots[0].texture
            self.assertEqual(texture.name, 'det\det_leaves')

    def _get_compatible_material(self):
        prefs = utils.get_preferences()
        tex_folder = prefs.textures_folder
        prefs.textures_folder = 'gamedata/textures/'
        img = bpy.data.images.new('texture', 0, 0)
        img.source = 'FILE'
        img.filepath = 'gamedata/textures/eye.dds'
        mat = _create_compatible_material_object()
        if bpy.app.version >= (2, 80, 0):
            node_tree = mat.node_tree
            tex = node_tree.nodes.new('ShaderNodeTexImage')
            tex.image = img
            tex.location.x -= 500
            princ_shader = node_tree.nodes['Principled BSDF']
            node_tree.links.new(
                tex.outputs['Color'],
                princ_shader.inputs['Base Color']
            )
            mts = None
        else:
            tex = bpy.data.textures.new('eye', type='IMAGE')
            tex.image = img
            mts = mat.texture_slots.add()
            mts.uv_layer = 'uvm'
            mts.texture = tex
        return mat, mts, tex


def _create_compatible_material_object():
    mat = bpy.data.materials.new('plmat')
    # Otherwise, this material will be initialized
    # with the default values (see #48).
    mat.xray.version = -1
    if bpy.app.version >= (2, 80, 0):
        mat.use_nodes = True
    return mat
