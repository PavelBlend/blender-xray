import bpy
from mathutils import Matrix, Euler, Quaternion
from .utils import is_exportable_bone, find_bone_exportable_parent, AppError
from .xray_envelope import Behaviour, Shape
from .xray_io import PackedWriter


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


def export_motion(pkw, action, ctx, armature):
    prepared_bones = _prepare_bones(armature)
    _ake_motion_data = _bake_motion_data if action.xray.autobake else _take_motion_data
    bones_animations = _ake_motion_data(action, armature, ctx, prepared_bones)
    _export_motion_data(pkw, action, bones_animations)


def _take_motion_data(bpy_act, bpy_armature, cx, prepared_bones):
    xr = bpy_act.xray
    fr = bpy_act.frame_range
    result = []
    for bone, xm in prepared_bones:
        data = []
        result.append((bone.name, data))

        g = bpy_act.groups.get(bone.name, None)
        if g is None:
            data.append(xm)
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

        for t in range(int(fr[0]), int(fr[1]) + 1):
            mat = xm * Matrix.Translation(evaluate_channels(chs_tr, t)) * frotmatrix(evaluate_channels(chs_rt, t)).to_4x4()
            data.append(mat)

    return result


def _bake_motion_data(action, armature, _, prepared_bones):
    exportable_bones = [(bone, matrix, []) for bone, matrix in prepared_bones]

    old_act = armature.animation_data.action
    old_frame = bpy.context.scene.frame_current
    try:
        armature.animation_data.action = action
        for frm in range(int(action.frame_range[0]), int(action.frame_range[1]) + 1):
            bpy.context.scene.frame_set(frm)
            bpy.context.scene.update()
            for pbone, mat, data in exportable_bones:
                data.append(mat * armature.convert_space(pbone, pbone.matrix, 'POSE', 'LOCAL'))
    finally:
        armature.animation_data.action = old_act
        bpy.context.scene.frame_set(old_frame)

    return [(pbone.name, animation) for pbone, _, animation in exportable_bones]


def _prepare_bones(armature):
    def prepare_bone(bone):
        mat = bone.matrix_local
        real_parent = find_bone_exportable_parent(bone)
        if real_parent:
            mat = real_parent.matrix_local.inverted() * mat
        else:
            mat = __matrix_bone_inv * mat
        return armature.pose.bones[bone.name], mat

    return [
        prepare_bone(bone)
        for bone in armature.data.bones if is_exportable_bone(bone)
    ]


def _export_motion_data(pkw, action, bones_animations):
    xray = action.xray
    pkw.puts(action.name)
    frange = action.frame_range
    pkw.putf('II', int(frange[0]), int(frange[1]))
    pkw.putf('f', xray.fps)
    pkw.putf('H', 6)  # version
    pkw.putf('<BH', xray.flags, xray.bonepart)
    pkw.putf('<ffff', xray.speed, xray.accrue, xray.falloff, xray.power)
    pkw.putf('H', len(bones_animations))
    for name, animation in bones_animations:
        pkw.puts(name)
        pkw.putf('B', 0)  # flags
        curves = ([], [], [], [], [], [])

        for mat in animation:
            trn = mat.to_translation()
            rot = mat.to_euler('ZXY')
            curves[0].append(+trn[0])
            curves[1].append(+trn[1])
            curves[2].append(-trn[2])
            curves[3].append(-rot[1])
            curves[4].append(-rot[0])
            curves[5].append(+rot[2])

        for curve in curves:
            pkw.putf('BB', Behaviour.CONSTANT.value, Behaviour.CONSTANT.value)
            cpkw = PackedWriter()
            ccnt = 0
            pval = 0
            for frm, val in enumerate(curve):
                if (frm != 0) and (abs(pval - val) < 0.0001):
                    continue
                cpkw.putf('ffB', val, frm / xray.fps, Shape.STEPPED.value)
                pval = val
                ccnt += 1
            pkw.putf('H', ccnt)
            pkw.putp(cpkw)


def export_motions(pw, actions, cx, bpy_armature):
    pw.putf('I', len(actions))
    for a in actions:
        export_motion(pw, a, cx, bpy_armature)
