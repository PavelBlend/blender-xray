import tests
import os
import bpy
import io_scene_xray
import re


class TestMotionMarks(tests.utils.XRayTestCase):

    def test_object_marks_export(self):
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


def _create_export_data():
    mesh_obj = _create_object()

    obj = _create_armature((mesh_obj, ))
    obj.xray.isroot = True

    act = bpy.data.actions.new('test_act')
    act.use_fake_user = True
    motion = obj.xray.motions_collection.add()
    motion.name = act.name

    bpy.ops.object.select_all(action='SELECT')

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
