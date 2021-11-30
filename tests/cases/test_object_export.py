from tests import utils

import bpy
import io_scene_xray
import re


class TestObjectExport(utils.XRayTestCase):
    def test_export_single(self):
        # Arrange
        self._create_objects()

        # Act
        bpy.ops.xray_export.object_file(
            object='tobj1', filepath=self.outpath('test.object'),
            texture_name_from_image_path=False
        )

        # Assert
        self.assertOutputFiles({
            'test.object'
        })

    def test_export_multi(self):
        # Arrange
        objs = self._create_objects()
        objs[0].location = (1, 2, 3)

        # Act
        bpy.ops.xray_export.object(
            objects='tobj1,tobj2', directory=self.outpath(),
            fmt_version='cscop',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertOutputFiles({
            'tobj1.object',
            'a/b/tobj2.object'
        })

    def test_export_multi_notusing_paths(self):
        # Arrange
        self._create_objects()

        # Act
        bpy.ops.xray_export.object(
            objects='tobj1,tobj2', directory=self.outpath(),
            use_export_paths=False,
            texture_name_from_image_path=False
        )

        # Assert
        self.assertOutputFiles({
            'tobj1.object',
            'tobj2.object'
        })

    def test_export_project(self):
        # Arrange
        self._create_objects()
        for obj in bpy.data.objects:
            if bpy.app.version >= (2, 80, 0):
                obj.select_set(obj.name in {'tobj1', 'tobj2'})
            else:
                obj.select = obj.name in {'tobj1', 'tobj2'}

        # Act
        bpy.ops.xray_export.project(
            filepath=self.outpath(),
            use_selection=True
        )
        self.assertOutputFiles({
            'tobj1.object',
            'a/b/tobj2.object'
        })

    def test_obsolete_bones(self):
        # Arrange
        objs = self._create_objects()

        obj = _create_armature((objs[0], ))
        utils.set_active_object(obj)
        arm = obj.data
        arm.bones['tbone'].xray.shape.type = '2'
        arm.bones['tbone'].xray.shape.sph_rad = 1

        # Act
        bpy.ops.xray_export.object(
            objects='tobj', directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False,
        )

        # Assert
        self.assertOutputFiles({
            'tobj.object',
        })
        self.assertReportsContains(
            'WARNING',
            re.compile('Bone edited with a different version of this plugin')
        )

    def test_empty_bone_groups(self):
        # Arrange
        arm = bpy.data.armatures.new('tarm')
        obj = bpy.data.objects.new('tobj', arm)
        utils.link_object(obj)
        utils.set_active_object(obj)
        b_exp0, b_non0, b_exp1, b_non1 = (
            'b-exportable0',
            'b-non-exportable0',
            'b-exportable1',
            'b-non-exportable1'
        )
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            for n in (b_exp0, b_non0, b_exp1, b_non1):
                bone = arm.edit_bones.new(n)
                bone.tail.y = 1
            for n in (b_non0, b_exp1, b_non1):
                bone = arm.edit_bones[n]
                parent = arm.edit_bones[b_exp0]
                bone.parent = parent
        finally:
            bpy.ops.object.mode_set(mode='POSE')
        bg_exp = obj.pose.bone_groups.new(name='bg-only-exportable')
        bg_mix = obj.pose.bone_groups.new(name='bg-mixed')
        bg_non = obj.pose.bone_groups.new(name='bg-only-non-exportable')
        bg_emp = obj.pose.bone_groups.new(name='bg-empty')
        obj.pose.bones[b_exp0].bone_group = bg_exp
        obj.pose.bones[b_non0].bone_group = bg_mix
        obj.pose.bones[b_exp1].bone_group = bg_mix
        obj.pose.bones[b_non0].bone_group = bg_non
        arm.bones[b_non0].xray.exportable = False
        arm.bones[b_non1].xray.exportable = False

        bmesh = utils.create_bmesh((
            (0, 0, 0),
            (-1, -1, 0), (+1, -1, 0), (+1, +1, 0), (-1, +1, 0),
        ), ((0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)), True)
        obj_me = utils.create_object(bmesh, True)
        obj_me.parent = obj
        obj_me.xray.isroot = False
        arm_mod = obj_me.modifiers.new('Armature', 'ARMATURE')
        arm_mod.object = obj
        vertex_group = obj_me.vertex_groups.new(name='b-exportable0')
        vertex_group.add(range(len(obj_me.data.vertices)), 1.0, 'REPLACE')

        # Act
        bpy.ops.xray_export.object(
            objects='tobj', directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False,
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertOutputFiles({
            'tobj.object',
        })
        content = self.getFileSafeContent('tobj.object')
        self.assertRegex(content, re.compile(bytes(b_exp0, 'cp1251')))
        self.assertRegex(content, re.compile(bytes(b_exp1, 'cp1251')))
        self.assertNotRegex(content, re.compile(bytes(b_non0, 'cp1251')))
        self.assertNotRegex(content, re.compile(bytes(b_non1, 'cp1251')))
        self.assertRegex(content, re.compile(bytes(bg_exp.name, 'cp1251')))
        self.assertRegex(content, re.compile(bytes(bg_mix.name, 'cp1251')))
        self.assertNotRegex(content, re.compile(bytes(bg_non.name, 'cp1251')))
        self.assertNotRegex(content, re.compile(bytes(bg_emp.name, 'cp1251')))

    def test_export_with_empty(self):
        # Arrange
        root = bpy.data.objects.new('empty', None)
        utils.link_object(root)

        objs = self._create_objects()
        obj = _create_armature((objs[0], ))
        obj.parent = root

        utils.set_active_object(root)

        # Act
        bpy.ops.xray_export.object_file(
            object='empty', filepath=self.outpath('test.object'),
            texture_name_from_image_path=False
        )

        # Assert
        self.assertOutputFiles({
            'test.object'
        })

    def test_export_no_uvmap(self):
        # Arrange
        self._create_objects(create_uv=False)

        # Act
        bpy.ops.xray_export.object_file(
            object='tobj1', filepath=self.outpath('test.object'),
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('Mesh-object has no UV-map')
        )

    def test_export_no_material(self):
        # Arrange
        self._create_objects(create_material=False)

        # Act
        bpy.ops.xray_export.object_file(
            object='tobj1', filepath=self.outpath('test.object'),
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('Object has no material: "{0}"'.format('tobj1'))
        )

    def _create_objects(self, create_uv=True, create_material=True):
        bmesh = utils.create_bmesh((
            (0, 0, 0),
            (-1, -1, 0), (+1, -1, 0), (+1, +1, 0), (-1, +1, 0),
        ), ((0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)), create_uv)

        objs = []
        for i in range(3):
            obj = utils.create_object(bmesh, create_material)
            obj.name = 'tobj%d' % (i + 1)
            objs.append(obj)
        objs[1].xray.export_path = 'a/b'
        return objs

    def test_export_split_normals(self):
        # Arrange
        self._create_objects()

        # Act
        bpy.ops.xray_export.object_file(
            object='tobj1', filepath=self.outpath('test_split_normals.object'),
            texture_name_from_image_path=False, smoothing_out_of='SPLIT_NORMALS'
        )

        # Assert
        self.assertOutputFiles({
            'test_split_normals.object'
        })

    def test_merge_objects(self):
        # Arrange
        objs = self._create_objects()
        arm_obj = _create_armature(objs)
        utils.set_active_object(arm_obj)
        objs[0].modifiers.new('subsurf', 'SUBSURF')

        # Act
        bpy.ops.xray_export.object(
            objects='tobj', directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False,
        )

        # Assert
        self.assertOutputFiles({
            'tobj.object',
        })
        self.assertReportsContains(
            'WARNING',
            re.compile('Mesh-objects have been merged')
        )


def _create_armature(targets):
    arm = bpy.data.armatures.new('tarm')
    obj = bpy.data.objects.new('tobj', arm)
    utils.link_object(obj)
    utils.set_active_object(obj)

    bpy.ops.object.mode_set(mode='EDIT')
    try:
        bone = arm.edit_bones.new('tbone')
        bone.tail.y = 1
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')

    for target in targets:
        target.modifiers.new(name='Armature', type='ARMATURE').object = obj
        target.parent = obj
        grp = target.vertex_groups.new(name='tbone')
        vertices_count = len(target.data.vertices)
        grp.add(range(vertices_count), 1, 'REPLACE')
        grp = target.vertex_groups.new(name=io_scene_xray.utils.BAD_VTX_GROUP_NAME)
        grp.add([vertices_count], 1, 'REPLACE')

    return obj
