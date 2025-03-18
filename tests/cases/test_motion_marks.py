import tests
import os
import bpy
import io_scene_xray
import re


class TestMotionMarks(tests.utils.XRayTestCase):

    def test_marks_export(self):
        # Arrange
        _create_export_data()

        # Act
        bpy.ops.xray_export.object(
            objects='tobj',
            directory=self.outpath(),
            export_motions=True,
            fmt_version='cscop'
        )
        bpy.ops.xray_export.skls(
            directory=self.outpath(),
            fmt_ver='cscop'
        )
        bpy.ops.xray_export.ogf(
            directory=self.outpath(),
            export_motions=True,
            fmt_version='cscop'
        )
        bpy.ops.xray_export.omf(
            directory=self.outpath(),
            fmt_ver='cscop'
        )

        # Assert
        self.assertOutputFiles({
            'tobj.object',
            'tobj.skls',
            'tobj.ogf',
            'tobj.omf'
        })

    def test_marks_import(self):
        # Act
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_marks.object'}],
            fmt_version='cscop',
            import_motions=True
        )
        bpy.ops.xray_import.ogf(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_marks.ogf'}],
            import_motions=True
        )

        # Assert
        object_act = bpy.data.actions['test_action_object']
        ogf_act = bpy.data.actions['test_action_ogf']

        mark_names = ('Left', 'Right')

        for act in (object_act, ogf_act):
            xray = act.xray

            self.assertEqual(xray.marks_bone, 'root_bone')
            self.assertEqual(len(xray.marks_collection), 2)

            for mark_name in mark_names:
                has_mark_fcurve = False
                for fcurve in act.fcurves:
                    data_path = 'pose.bones["root_bone"]["{}"]'.format(mark_name)
                    if fcurve.data_path == data_path:
                        has_mark_fcurve = True
                        self.assertEqual(bool(len(fcurve.keyframe_points)), True)

                self.assertEqual(has_mark_fcurve, True)


def _create_export_data():
    mesh_obj = _create_object()

    obj = _create_armature((mesh_obj, ))
    obj.xray.isroot = True

    act = bpy.data.actions.new('test_act')
    act.use_fake_user = True
    motion = obj.xray.motions_collection.add()
    motion.name = act.name

    bpy.ops.object.select_all(action='DESELECT')
    tests.utils.set_active_object(obj)
    tests.utils.select_object(obj)

    for bone in obj.pose.bones:
        data_path = 'pose.bones["{}"]'.format(bone.name)
        for curve_name in ('location', 'rotation_euler'):
            for channel in range(3):
                fcurve = act.fcurves.new(
                    '{0}.{1}'.format(data_path, curve_name),
                    action_group=bone.name,
                    index=channel
                )
                keyframes = fcurve.keyframe_points
                keyframes.add(count=2)
                for index, frame in enumerate((0, 10)):
                    keyframes[index].co = (frame, index / 10)

    obj['xray_current_action'] = act.name
    bone = obj.pose.bones[0]
    bone['Left'] = 0.0
    bone['Right'] = 0.0
    xray = act.xray
    xray.marks_bone = bone.name
    mark_item = xray.marks_collection.add().mark = 'Left'
    mark_item = xray.marks_collection.add().mark = 'Right'
    data_path = 'pose.bones["{}"]'.format(bone.name)
    for mark_name in ('Left', 'Right'):
        fcurve = act.fcurves.new(
            '{0}["{1}"]'.format(data_path, mark_name),
            action_group=bone.name
        )
        keyframes = fcurve.keyframe_points
        keyframes.add(count=3)
        frames = (0, 2, 6)
        values = (0.0, 1.0, 0.0)
        for index, (frame, value) in enumerate(zip(frames, values)):
            keyframes[index].co = (frame, value)
            keyframes[index].interpolation = 'CONSTANT'


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
    tests.utils.link_object(obj)
    tests.utils.set_active_object(obj)

    bpy.ops.object.mode_set(mode='EDIT')
    try:
        bone = create_bone('tbone', (0, 1, 0))
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')

    bgroups = tests.utils.get_bone_groups(obj)
    bgroup = bgroups.new(name='default')
    tests.utils.assign_bone_group(obj, 'tbone', bgroup)

    for target in targets:
        target.modifiers.new(name='Armature', type='ARMATURE').object = obj
        target.parent = obj
        grp = target.vertex_groups.new(name='tbone')
        vertices_count = len(target.data.vertices)
        grp.add(range(vertices_count), 1, 'REPLACE')

    return obj


def _create_object(create_uv=True, create_material=True):
    bmesh = tests.utils.create_bmesh((
        (0, 0, 0),
        (-1, -1, 0), (+1, -1, 0), (+1, +1, 0), (-1, +1, 0),
    ), ((0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)), create_uv)

    obj = tests.utils.create_object(bmesh, create_material)
    obj.name = 'tmesh'

    return obj
