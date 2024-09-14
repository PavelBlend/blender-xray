from tests import utils

import os
import bpy
import io_scene_xray
import re


class TestObjectExport(utils.XRayTestCase):
    def test_export_single(self):
        # Arrange
        self._create_objects()

        # Act
        bpy.ops.xray_export.object_file(
            object='tobj1',
            filepath=self.outpath('test.object'),
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
            objects='tobj1,tobj2',
            directory=self.outpath(),
            fmt_version='cscop',
            texture_name_from_image_path=False,
            use_export_paths=True
        )

        # Assert
        self.assertOutputFiles({
            'tobj1.object',
            'a/b/tobj2.object'
        })

    def test_export_using_context(self):
        # remove default objects (cube, camera, lamp)
        for obj in bpy.data.objects:
            if bpy.app.version < (2, 79, 0):
                bpy.context.scene.objects.unlink(obj)
                obj.user_clear()
            bpy.data.objects.remove(obj)

        # Arrange
        self._create_objects()
        ob1 = bpy.data.objects['tobj1']
        ob2 = bpy.data.objects['tobj2']
        ob3 = bpy.data.objects['tobj3']
        ob2.xray.isroot = False
        ob3.xray.isroot = False
        ob2.parent = ob1
        ob3.parent = ob1
        bpy.ops.object.empty_add()
        ob1.name = 'root_obj'
        bpy.ops.object.select_all(action='SELECT')

        # Act
        bpy.ops.xray_export.object(
            directory=self.outpath(),
            texture_name_from_image_path=False,
            use_export_paths=False
        )

        # Assert
        self.assertOutputFiles({'root_obj.object', })

    def test_export_without_selection(self):
        # remove default objects (cube, camera, lamp)
        for obj in bpy.data.objects:
            if bpy.app.version < (2, 79, 0):
                bpy.context.scene.objects.unlink(obj)
                obj.user_clear()
            bpy.data.objects.remove(obj)

        # Act
        bpy.ops.xray_export.object(
            directory=self.outpath(),
            texture_name_from_image_path=False,
            use_export_paths=False
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('No root-objects found')
        )

        # Arrange
        self._create_objects()
        bpy.ops.object.select_all(action='DESELECT')

        # Act
        bpy.ops.xray_export.object(
            directory=self.outpath(),
            texture_name_from_image_path=False,
            use_export_paths=False
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('Too many root-objects found, but none selected')
        )

        # Arrange
        ob2 = bpy.data.objects['tobj2']
        if bpy.app.version < (2, 79, 0):
            bpy.context.scene.objects.unlink(ob2)
            ob2.user_clear()
        bpy.data.objects.remove(ob2)

        ob3 = bpy.data.objects['tobj3']
        if bpy.app.version < (2, 79, 0):
            bpy.context.scene.objects.unlink(ob3)
            ob3.user_clear()
        bpy.data.objects.remove(ob3)

        # Act
        bpy.ops.xray_export.object(
            directory=self.outpath(),
            texture_name_from_image_path=False,
            use_export_paths=False
        )

        # Assert
        self.assertOutputFiles({'tobj1.object', })

    def test_export_multi_notusing_paths(self):
        # Arrange
        self._create_objects()

        # Act
        bpy.ops.xray_export.object(
            objects='tobj1,tobj2',
            directory=self.outpath(),
            use_export_paths=False,
            texture_name_from_image_path=False
        )

        # Assert
        self.assertOutputFiles({
            'tobj1.object',
            'tobj2.object'
        })

    def test_many_uvs_and_not_used_mat(self):
        # Arrange
        obj = self._create_objects()[0]

        # set export path
        obj.xray.export_path = 'test'

        # add new uv layer
        if bpy.app.version >= (2, 80, 0):
            obj.data.uv_layers.new(name='test')
        else:
            obj.data.uv_textures.new(name='test')

        # add not used material
        mat = bpy.data.materials.new('test')
        obj.data.materials.append(mat)

        # add empty material slot
        utils.set_active_object(obj)
        bpy.ops.object.material_slot_add()

        # Act
        bpy.ops.xray_export.object_file(
            object='tobj1',
            filepath=self.outpath('test.object'),
            texture_name_from_image_path=False,
            use_export_paths=True
        )

        # Assert
        self.assertReportsContains(
            'WARNING',
            re.compile('Object has more than one UV-map. Active UV-map exported')
        )
        self.assertOutputFiles({
            os.path.join('test', 'test.object'),
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
            re.compile('Bone edited with a different version of this addon')
        )

    def test_bone_names(self):
        # Arrange
        objs = self._create_objects()

        obj = _create_armature((objs[0], ))
        utils.set_active_object(obj)
        arm = obj.data
        arm.bones[0].name = arm.bones[0].name.capitalize()

        # Act
        bpy.ops.xray_export.object(
            objects='tobj',
            directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False
        )

        # Assert
        self.assertOutputFiles({'tobj.object', })
        self.assertReportsContains(
            'WARNING',
            re.compile('Bone name has been saved without uppercase characters')
        )

    def test_bone_ik_flags(self):
        # Arrange
        objs = self._create_objects()

        obj = _create_armature((objs[0], ))
        utils.set_active_object(obj)
        arm = obj.data
        arm.bones[0].xray.ikflags_breakable = True
        obj.xray.flags_simple = 'dy'

        # Act
        bpy.ops.xray_export.object(
            objects='tobj',
            directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False
        )

        # Assert
        self.assertOutputFiles({'tobj.object', })

    def test_bone_ik_limits(self):
        # Arrange
        objs = self._create_objects()

        obj = _create_armature((objs[0], ))
        utils.set_active_object(obj)
        arm = obj.data
        arm.xray.joint_limits_type = 'IK'

        # Act
        bpy.ops.xray_export.object(
            objects='tobj',
            directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False
        )

        # Assert
        self.assertOutputFiles({'tobj.object', })

    def test_bone_friction_and_mass(self):
        # Arrange
        objs = self._create_objects()

        obj = _create_armature((objs[0], ))
        utils.set_active_object(obj)
        arm = obj.data
        bone = arm.bones[0]
        bone.xray.friction = 0.5
        bone.xray.mass.value = 2.0

        # Act
        bpy.ops.xray_export.object(
            objects='tobj',
            directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False
        )

        # Assert
        self.assertOutputFiles({'tobj.object', })

    def test_bone_duplicates(self):
        # Arrange
        objs = self._create_objects()

        obj = _create_armature((objs[0], ))
        utils.set_active_object(obj)

        # add duplicated bones
        bpy.ops.object.mode_set(mode='EDIT')

        try:
            root_bone = obj.data.edit_bones[0]
            name = root_bone.name.upper()
            dupli_bone = obj.data.edit_bones.new(name)
            dupli_bone.parent = root_bone
            dupli_bone.tail.y = 1

            name = root_bone.name.capitalize()
            dupli_bone = obj.data.edit_bones.new(name)
            dupli_bone.parent = root_bone
            dupli_bone.tail.y = 1

        finally:
            bpy.ops.object.mode_set(mode='OBJECT')

        # Act
        bpy.ops.xray_export.object(
            objects='tobj',
            directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('Object has duplicate bones')
        )

    def test_ungroupped_verts(self):
        # Arrange
        objs = self._create_objects()
        mesh_obj = objs[0]

        obj = _create_armature((mesh_obj, ))
        utils.set_active_object(obj)

        # remove vertex group
        group = mesh_obj.vertex_groups[0]
        mesh_obj.vertex_groups.remove(group)

        # Act
        bpy.ops.xray_export.object(
            objects='tobj',
            directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('Mesh-object has vertices that don\'t have vertex groups')
        )

    def test_nonexp_vert_groups(self):
        # Arrange
        objs = self._create_objects()
        mesh_obj = objs[0]

        obj = _create_armature((mesh_obj, ))
        utils.set_active_object(obj)

        # add non-exportable bone
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            nonexp_bone = obj.data.edit_bones.new('non_exportable')
            nonexp_bone.tail.y = 1
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        obj.data.bones['non_exportable'].xray.exportable = False

        # assign vertex for non-exportable group
        grp = mesh_obj.vertex_groups.new(name='non_exportable')
        grp.add([0, ], 1, 'REPLACE')
        mesh_obj.vertex_groups['tbone'].remove([0, ])

        # Act
        bpy.ops.xray_export.object(
            objects='tobj',
            directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('Mesh-object has vertices that are not tied to any exportable bones')
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
        self.assertReportsNotContains('ERROR')
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
            object='empty',
            filepath=self.outpath('test.object'),
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
            object='tobj1',
            filepath=self.outpath('test.object'),
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
            object='tobj1',
            filepath=self.outpath('test.object'),
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('Object has no material: "{0}"'.format('tobj1'))
        )

    def _create_objects(self, create_uv=True, create_material=True, count=3):
        bmesh = utils.create_bmesh((
            (0, 0, 0),
            (-1, -1, 0), (+1, -1, 0), (+1, +1, 0), (-1, +1, 0),
        ), ((0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)), create_uv)

        objs = []
        for i in range(count):
            obj = utils.create_object(bmesh, create_material)
            obj.name = 'tobj%d' % (i + 1)
            objs.append(obj)
        if len(objs) > 1:
            objs[1].xray.export_path = 'a/b'
        return objs

    def test_export_split_normals(self):
        # Arrange
        self._create_objects()

        # Act
        bpy.ops.xray_export.object_file(
            object='tobj1',
            filepath=self.outpath('test_split_normals.object'),
            texture_name_from_image_path=False,
            smoothing_out_of='SPLIT_NORMALS'
        )

        # Assert
        self.assertOutputFiles({
            'test_split_normals.object'
        })

    def test_merge_objects(self):
        # Arrange
        objs = self._create_objects()
        objs[0].modifiers.new('subsurf', 'SUBSURF')
        arm_obj = _create_armature(objs)
        utils.set_active_object(arm_obj)

        # Act
        bpy.ops.xray_export.object(
            objects='tobj',
            directory=self.outpath(),
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

    def test_export_skeletal_object(self):
        # Arrange
        objs = self._create_objects()

        obj = _create_armature((objs[0], ))
        obj.name = 'skeletal_object_soc_format'
        obj.xray.lodref = 'test lod reference'
        obj.xray.userdata = 'test user data'
        for ref_index in range(3):
            ref = obj.xray.motionrefs_collection.add()
            ref.name = 'motion_reference_' + str(ref_index)
        utils.set_active_object(obj)

        # Act
        bpy.ops.xray_export.object(
            objects='skeletal_object_soc_format',
            directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False
        )
        obj.name = 'skeletal_object_cop_format'
        bpy.ops.xray_export.object(
            objects='skeletal_object_cop_format',
            directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False,
            fmt_version='cscop'
        )

        # Assert
        self.assertOutputFiles({
            'skeletal_object_soc_format.object',
            'skeletal_object_cop_format.object'
        })
        self.assertReportsNotContains('ERROR')

    def test_fails_export_nonuniform_scaled_object(self):
        # Arrange
        root = bpy.data.objects.new('root', None)
        utils.link_object(root)
        root.scale = (1, 1, 1.000002)
        [obj_mesh] = self._create_objects(count=1)

        obj_arm = _create_armature((obj_mesh, ))
        obj_arm.parent = root
        utils.set_active_object(root)

        root.xray.isroot = True
        obj_arm.xray.isroot = False

        # Act
        bpy.ops.xray_export.object(
            objects=root.name,
            directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False
        )

        # Assert
        self.assertOutputFiles({})
        self.assertReportsContains('ERROR', re.compile('Object has an non-uniform scale: "tobj"'))

    def test_export_scaled_skeletal_object(self):
        # Arrange
        root = bpy.data.objects.new('root', None)
        utils.link_object(root)
        root.scale = (2, 2, 2)
        [obj_mesh] = self._create_objects(count=1)
        obj_mesh.parent = root
        obj_mesh.scale.x = 1.5

        obj_arm = _create_armature((obj_mesh, ))
        obj_arm.scale = (1.25, 1.25, 1.25)
        obj_arm.parent = root
        obj_arm.name = 'scaled_skeletal_object'
        utils.set_active_object(obj_mesh)

        # Act
        bpy.ops.xray_export.object(
            objects=obj_arm.name,
            directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False
        )

        # Assert
        self.assertReportsNotContains('ERROR')
        filename = obj_arm.name + '.object'
        self.assertOutputFiles({filename, })

        bpy.ops.xray_import.object(
            directory=self.outpath(),
            files=[{'name': filename}],
        )
        self.assertReportsNotContains('ERROR')

        dimensions = lambda name: bpy.data.objects[name].dimensions.to_tuple()
        self.assertEqual(dimensions('tobj1.001'), (7.5, 5.0, 0.0))
        self.assertEqual(dimensions(filename), (1.25, 2.5, 0.625))

    def test_export_incorrect_textures_folder(self):
        # Arrange
        self._create_objects()
        prefs = utils.get_preferences()
        prefs.textures_folder = 'incorrect_value'

        obj = bpy.data.objects['tobj1']
        mat = obj.data.materials[0]
        bpy_image = None
        if bpy.app.version >= (2, 80, 0):
            mat_nodes = mat.node_tree.nodes
            for node in mat_nodes:
                if node.bl_idname == 'ShaderNodeTexImage':
                    bpy_image = node.image
                    break
        else:
            bpy_image = mat.texture_slots[0].texture.image

        # Act
        bpy.ops.xray_export.object_file(
            object='tobj1',
            filepath=self.outpath('test.object')
        )

        # Assert
        self.assertOutputFiles({'test.object', })

        bpy_image.filepath = 'T:\\test.dds'

        # Act
        bpy.ops.xray_export.object_file(
            object='tobj1',
            filepath=self.outpath('test.object')
        )

        # Assert
        self.assertOutputFiles({'test.object', })

        bpy_image.filepath = 'T:\\folder\\folder_file.dds'

        # Act
        bpy.ops.xray_export.object_file(
            object='tobj1',
            filepath=self.outpath('test.object')
        )

        # Assert
        self.assertOutputFiles({'test.object', })

    def test_export_legacy_motion_refs(self):
        # Arrange
        obj = self._create_objects()[0]
        obj.xray.motionrefs = 'test legacy motion refs'

        # legacy soc
        bpy.ops.xray_export.object_file(
            object=obj.name,
            filepath=self.outpath('test.object'),
            fmt_version='soc',
            texture_name_from_image_path=False
        )

        self.assertOutputFiles({
            'test.object'
        })

        self.assertReportsNotContains()

        # legacy cop
        bpy.ops.xray_export.object_file(
            object=obj.name,
            filepath=self.outpath('test.object'),
            fmt_version='cscop',
            texture_name_from_image_path=False
        )

        self.assertOutputFiles({
            'test.object'
        })

        self.assertReportsNotContains()

        # add motion refs
        ref = obj.xray.motionrefs_collection.add()
        ref.name = 'test motion ref'

        # skipped soc
        bpy.ops.xray_export.object_file(
            object=obj.name,
            filepath=self.outpath('test.object'),
            fmt_version='soc',
            texture_name_from_image_path=False
        )

        self.assertOutputFiles({
            'test.object'
        })

        self.assertReportsContains(
            'WARNING',
            re.compile('Skipped motion references legacy data')
        )

        # skipped cop
        bpy.ops.xray_export.object_file(
            object=obj.name,
            filepath=self.outpath('test.object'),
            fmt_version='cscop',
            texture_name_from_image_path=False
        )

        self.assertOutputFiles({
            'test.object'
        })

        self.assertReportsContains(
            'WARNING',
            re.compile('Skipped motion references legacy data')
        )


def _create_armature(targets):
    def create_bone(name, tail, parent=None):
        bone = arm.edit_bones.new(name)
        bone.tail = tail
        if parent:
            bone.parent = parent
            bone.use_connect = True
            bone.tail += parent.tail
        return bone

    arm = bpy.data.armatures.new('tarm')
    obj = bpy.data.objects.new('tobj', arm)
    utils.link_object(obj)
    utils.set_active_object(obj)

    bpy.ops.object.mode_set(mode='EDIT')
    try:
        bone = create_bone('tbone', (0, 1, 0))
        bone = create_bone('tbone+x', (0.5, 0, 0), bone)
        bone = create_bone('tbone+z', (0, 0, 0.25), bone)
        bone = create_bone('tbone=0', (-0.5, -1, -0.25), bone)
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
