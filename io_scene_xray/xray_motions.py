from enum import Enum
from mathutils import Matrix, Euler
from .utils import find_bone_real_parent


class Shape(Enum):
    STEPPED = 4


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
        xm = bpy_bone.matrix_local.inverted()
        real_parent = find_bone_real_parent(bpy_bone)
        if real_parent:
            xm = xm * real_parent.matrix_local
        else:
            xm = xm * __matrix_bone
        xm.invert()
        envdata = []
        for t in range(int(fr[0]), int(fr[1]) + 1):
            tr = (g.channels[0].evaluate(t), g.channels[1].evaluate(t), g.channels[2].evaluate(t))
            rt = (g.channels[3].evaluate(t), g.channels[4].evaluate(t), g.channels[5].evaluate(t))
            mat = xm * Matrix.Translation(tr) * Euler(rt, rotmode).to_matrix().to_4x4()
            tr = mat.to_translation()
            rt = mat.to_euler('ZXY')
            envdata.append((t, tr[0], tr[1], -tr[2], -rt[1], -rt[0], rt[2]))
        for i in range(6):
            pw.putf('BB', 1, 1)
            pw.putf('H', len(envdata))
            for e in envdata:
                pw.putf('ffB', e[i + 1], e[0] / xr.fps, Shape.STEPPED.value)
