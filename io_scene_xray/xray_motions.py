from mathutils import Matrix, Euler, Quaternion
from .utils import is_exportable_bone, find_bone_exportable_parent, AppError
from .xray_envelope import Behaviour, Shape


__matrix_bone = Matrix(((1.0, 0.0, 0.0, 0.0), (0.0, 0.0, -1.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
__matrix_bone_inv = __matrix_bone.inverted()


def import_motion(pr, cx, bpy, bpy_armature, bonesmap, reported):
    act = bpy.data.actions.new(name=pr.gets())
    act.use_fake_user = True
    xr = act.xray
    pr.getf('II')  # range
    fps, ver = pr.getf('fH')
    xr.fps = fps
    if ver >= 6:
        xr.flags, xr.bonepart = pr.getf('<BH')
        xr.speed, xr.accrue, xr.falloff, xr.power = pr.getf('<ffff')
        for _1 in range(pr.getf('H')[0]):
            tmpfc = [act.fcurves.new('temp', i) for i in range(6)]
            try:
                times = {}
                bname = pr.gets()
                flags = pr.getf('B')[0]
                if flags != 0:
                    cx.report({'WARNING'}, 'bone "{}" flags == {}'.format(bname, flags))
                for i in range(6):
                    behaviours = pr.getf('BB')
                    if (behaviours[0] != 1) or (behaviours[1] != 1):
                        cx.report({'WARNING'}, 'bone "{}" behaviours == {}'.format(bname, behaviours))
                    fc = tmpfc[i]
                    for _3 in range(pr.getf('H')[0]):
                        v = pr.getf('f')[0]
                        t = pr.getf('f')[0] * fps
                        times[t] = True
                        fc.keyframe_points.insert(t, v)
                        shape = Shape(pr.getf('B')[0])
                        if shape != Shape.STEPPED:
                            pr.getf('HHH')
                            pr.getf('HHHH')
                bpy_bone = bpy_armature.data.bones.get(bname, None)
                if bpy_bone is None:
                    bpy_bone = bonesmap.get(bname.lower(), None)
                    if bpy_bone is None:
                        if bname not in reported:
                            cx.report({'WARNING'}, 'Object motions: bone {} not found'.format(bname))
                            reported.add(bname)
                        continue
                    if bname not in reported:
                        cx.report({'WARNING'}, 'Object motions: bone {} reference replaced to {}'.format(bname, bpy_bone.name))
                        reported.add(bname)
                    bname = bpy_bone.name
                dp = 'pose.bones["' + bname + '"]'
                fcs = [
                    act.fcurves.new(dp + '.location', 0, bname),
                    act.fcurves.new(dp + '.location', 1, bname),
                    act.fcurves.new(dp + '.location', 2, bname),
                    act.fcurves.new(dp + '.rotation_euler', 0, bname),
                    act.fcurves.new(dp + '.rotation_euler', 1, bname),
                    act.fcurves.new(dp + '.rotation_euler', 2, bname)
                ]
                xm = bpy_bone.matrix_local.inverted()
                real_parent = find_bone_exportable_parent(bpy_bone)
                if real_parent:
                    xm = xm * real_parent.matrix_local
                else:
                    xm = xm * __matrix_bone
                for t in times.keys():
                    tr = (tmpfc[0].evaluate(t), tmpfc[1].evaluate(t), -tmpfc[2].evaluate(t))
                    rt = (-tmpfc[4].evaluate(t), -tmpfc[3].evaluate(t), tmpfc[5].evaluate(t))
                    mat = xm * Matrix.Translation(tr) * Euler(rt, 'ZXY').to_matrix().to_4x4()
                    tr = mat.to_translation()
                    rt = mat.to_euler('ZXY')
                    for _4 in range(3):
                        fcs[_4 + 0].keyframe_points.insert(t, tr[_4])
                    for _4 in range(3):
                        fcs[_4 + 3].keyframe_points.insert(t, rt[_4])
            finally:
                for fc in tmpfc:
                    act.fcurves.remove(fc)
        if ver >= 7:
            for _1 in range(pr.getf('I')[0]):
                name = pr.gets()
                pr.skip((4 + 4) * pr.getf('I')[0])
                cx.report({'WARNING'}, 'Object motions: skipping unsupported feature: marker ' + name)
    else:
        raise Exception('unsupported motions version: {}'.format(ver))
    return act


def import_motions(pr, cx, bpy, bpy_armature):
    bonesmap = {b.name.lower(): b for b in bpy_armature.data.bones}
    reported = set()
    for _ in range(pr.getf('I')[0]):
        import_motion(pr, cx, bpy, bpy_armature, bonesmap, reported)


def export_motion(pw, bpy_act, cx, bpy_armature):
    xr = bpy_act.xray
    pw.puts(bpy_act.name)
    fr = bpy_act.frame_range
    pw.putf('II', int(fr[0]), int(fr[1]))
    pw.putf('f', xr.fps)
    pw.putf('H', 6)  # version
    pw.putf('<BH', xr.flags, xr.bonepart)
    pw.putf('<ffff', xr.speed, xr.accrue, xr.falloff, xr.power)
    exportable_bones = [b for b in bpy_armature.data.bones if is_exportable_bone(b)]
    pw.putf('H', len(exportable_bones))
    for bpy_bone in exportable_bones:
        pw.puts(bpy_bone.name)
        pw.putf('B', 0)  # flags

        xm = bpy_bone.matrix_local.inverted()
        real_parent = find_bone_exportable_parent(bpy_bone)
        if real_parent:
            xm = xm * real_parent.matrix_local
        else:
            xm = xm * __matrix_bone
        xm.invert()

        g = bpy_act.groups.get(bpy_bone.name, None)
        if g is None:
            trn = xm.to_translation()
            rot = xm.to_euler('ZXY')
            for value in (trn[0], trn[1], -trn[2], -rot[1], -rot[0], rot[2]):
                pw.putf('BBH', Behaviour.CONSTANT.value, Behaviour.CONSTANT.value, 1)
                pw.putf('ffB', value, 0, Shape.STEPPED.value)
            continue
        rotmode = bpy_armature.pose.bones[g.name].rotation_mode
        chs_tr, chs_rt = [None, None, None], None

        def frotmatrix(rt): pass
        if len(rotmode) == 3:
            def frotmatrix(rt): return Euler(rt, rotmode).to_matrix()
            chs_rt = [None, None, None]
        elif rotmode == 'QUATERNION':
            def frotmatrix(rt): return Quaternion(rt).to_matrix()
            chs_rt = [None, None, None, None]
        else:
            raise AppError('Motions: {} bone {} uses unsupported rotation mode {}'.format(bpy_act.name, g.name, rotmode))

        skipped_paths = set()
        for c in g.channels:
            path = c.data_path
            chs = None
            if path.endswith('.location'):
                chs = chs_tr
            elif path.endswith('.rotation_euler'):
                if len(rotmode) == 3:
                    chs = chs_rt
            elif path.endswith('.rotation_quaternion'):
                if rotmode == 'QUATERNION':
                    chs = chs_rt
            if chs is None:
                if path not in skipped_paths:
                    cx.report({'WARNING'}, 'Motions: {} bone {} has curve {} which not supported by rotation mode {}, skipping'.format(bpy_act.name, g.name, path, rotmode))
                skipped_paths.add(path)
                continue
            chs[c.array_index] = c

        def evaluate_channels(channels, time):
            return (c.evaluate(time) if c else 0 for c in channels)

        envdata = []
        for t in range(int(fr[0]), int(fr[1]) + 1):
            mat = xm * Matrix.Translation(evaluate_channels(chs_tr, t)) * frotmatrix(evaluate_channels(chs_rt, t)).to_4x4()
            tr = mat.to_translation()
            rt = mat.to_euler('ZXY')
            envdata.append((t, tr[0], tr[1], -tr[2], -rt[1], -rt[0], rt[2]))
        for i in range(6):
            pw.putf('BB', Behaviour.CONSTANT.value, Behaviour.CONSTANT.value)
            pw.putf('H', len(envdata))
            for e in envdata:
                pw.putf('ffB', e[i + 1], e[0] / xr.fps, Shape.STEPPED.value)


def export_motions(pw, actions, cx, bpy_armature):
    pw.putf('I', len(actions))
    for a in actions:
        export_motion(pw, a, cx, bpy_armature)
