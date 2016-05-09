from mathutils import Matrix, Euler, Quaternion
from .utils import find_bone_real_parent, AppError
from .xray_envelope import Behaviour, Shape


__matrix_bone = Matrix(((1.0, 0.0, 0.0, 0.0), (0.0, 0.0, -1.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
__matrix_bone_inv = __matrix_bone.inverted()


def export_motions(pw, bpy_act, cx, bpy_armature=None):
    xr = bpy_act.xray
    pw.puts(bpy_act.name)
    fr = bpy_act.frame_range
    pw.putf('II', int(fr[0]), int(fr[1]))
    pw.putf('f', xr.fps)
    pw.putf('H', 6)  # version
    pw.putf('<BH', xr.flags, xr.bonepart)
    pw.putf('<ffff', xr.speed, xr.accrue, xr.falloff, xr.power)
    pw.putf('H', len(bpy_act.groups))
    for g in bpy_act.groups:
        pw.puts(g.name)
        pw.putf('B', 0)  # flags
        bpy_bone = bpy_armature.data.bones[g.name]
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

        xm = bpy_bone.matrix_local.inverted()
        real_parent = find_bone_real_parent(bpy_bone)
        if real_parent:
            xm = xm * real_parent.matrix_local
        else:
            xm = xm * __matrix_bone
        xm.invert()
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
