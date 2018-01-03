from tests import utils

import bmesh
import bpy
import re


class TestObjectImport(utils.XRayTestCase):
    def test_import_broken(self):
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_broken.object'}],
        )
        self.assertReportsContains('WARNING', re.compile('Unsupported bone shape type'))
        self.assertReportsContains('WARNING', re.compile('Unsupported bone ikjoint type'))

        log = self.getFullLogAsText()
        self.assertRegex(log, re.escape("file(path='"))
        self.assertRegex(log, re.escape("bone(name='Bone')"))

    def test_import_no_bone_shapes(self):
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_armature.object'}],
            shaped_bones=False
        )
        self.assertReportsNotContains('WARNING')
        pbones = bpy.context.active_object.pose.bones
        self.assertIsNone(pbones[0].custom_shape)
        bones = bpy.context.active_object.data.bones
        fakes = [b.name for b in bones if b.name.endswith('.fake')]
        self.assertEqual(fakes, ['Bone1.fake'])
        self.assertEqual(pbones['Bone'].bone_group.name, 'GroupA')
        self.assertEqual(pbones['Bone1'].bone_group.name, 'GroupB')
        self.assertTrue(bones['Bone1'].use_connect)

    def test_import_no_fakes(self):
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_armature.object'}],
            fake_bones=False,
        )
        self.assertReportsNotContains('WARNING')
        bones = bpy.context.active_object.data.bones
        fakes = [b.name for b in bones if b.name.endswith('.fake')]
        self.assertEqual(fakes, [])
        self.assertFalse(bones['Bone1'].use_connect)

    def test_import_pretty(self):
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_armature.object'}],
            pretty_bones=True,
        )
        self.assertReportsNotContains('WARNING')
        bones = bpy.context.active_object.data.bones
        fakes = [b.name for b in bones if b.name.endswith('.fake')]
        self.assertEqual(fakes, [])
        self.assertTrue(bones['Bone1'].use_connect)

    def test_import_uv(self):
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.object'}],
        )
        self.assertReportsNotContains('WARNING')
        obj = bpy.data.objects['test_fmt.object']
        self.assertEqual(obj.material_slots[0].material.texture_slots[0].uv_layer, 'uvm')
        self.assertEqual(len(obj.data.uv_layers), 1)
        self.assertEqual(obj.data.uv_layers[0].name, 'uvm')
        self.assertEqual(len(obj.data.uv_textures), 1)
        self.assertEqual(obj.data.uv_textures[0].name, 'uvm')
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        uvl = bm.loops.layers.uv.verify()
        bm.faces.ensure_lookup_table()
        for l, e in zip(bm.faces[0].loops, [(1, 0), (0, 1), (0, 0)]):
            uv = l[uvl].uv
            self.assertEqual(uv.to_tuple(), e)

    def test_import_vmrefs(self):
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_vmrefs.object'}],
        )
        self.assertReportsNotContains('WARNING')
        obj = bpy.data.objects['testShape']
        self.assertEqual(len(obj.data.vertices), 6)
