from enum import Enum
from .xray_io import PackedWriter
from .utils import mkstruct


class Behaviour(Enum):
    RESET = 0
    CONSTANT = 1
    REPEAT = 2
    OSCILLATE = 3
    OFFSET_REPEAT = 4
    LINEAR = 5


class Shape(Enum):
    TCB = 0  # Kochanek-Bartels
    HERMITE = 1
    BEZIER_1D = 2  # obsolete, equivalent to HERMITE
    LINEAR = 3
    STEPPED = 4
    BEZIER_2D = 5


def import_envelope(pr, fc, fps, kv, warn=print):
    b0, b1 = map(Behaviour, pr.getf('BB'))

    if b0 != b1:
        warn('Envelope: different behaviours: {} != {}, {} replaced with {}'.format(b0.name, b1.name, b1.name, b0.name))
        b1 = b0
    if b0 == Behaviour.CONSTANT:
        fc.extrapolation = 'CONSTANT'
    elif b0 == Behaviour.LINEAR:
        fc.extrapolation = 'LINEAR'
    else:
        b1 = Behaviour.CONSTANT
        warn('Envelope: behaviour {} not supported, replaced with {}'.format(b0.name, b1.name))
        b0 = b1
        fc.extrapolation = 'CONSTANT'

    replace_unsupported_to = 'BEZIER'
    unsupported_occured = set()
    fckf = fc.keyframe_points
    kf = None
    for _ in range(pr.getf('H')[0]):
        v, t = pr.getf('ff')
        sh = Shape(pr.getf('B')[0])
        if kf:
            if sh == Shape.LINEAR:
                kf.interpolation = 'LINEAR'
            elif sh == Shape.STEPPED:
                kf.interpolation = 'CONSTANT'
            else:
                unsupported_occured.add(sh.name)
                kf.interpolation = replace_unsupported_to
        kf = fckf.insert(t * fps, v * kv)
        if sh != Shape.STEPPED:
            pr.getf('HHH')
            pr.getf('HHHH')

    if len(unsupported_occured):
        warn('Envelope: unsupported shapes: {}, replaced by {}'.format(unsupported_occured, replace_unsupported_to))


KF = mkstruct('KeyFrame', ['time', 'value', 'shape'])
EPSILON = 0.0001

def export_envelope(pw, fc, fps, kv, warn=print, epsilon=EPSILON):
    b = None
    if fc.extrapolation == 'CONSTANT':
        b = Behaviour.CONSTANT
    elif fc.extrapolation == 'LINEAR':
        b = Behaviour.LINEAR
    else:
        b = Behaviour.LINEAR
        warn('Envelope: extrapolation {} not supported, replaced with {}'.format(fc.extrapolation, b.name))
    pw.putf('BB', b.value, b.value)

    replace_unsupported_to = Shape.TCB
    unsupported_occured = set()

    def generate_keys(keyframe_points):
        pkf = None
        for ckf in keyframe_points:
            shape = Shape.STEPPED
            if pkf is not None:
                if pkf.interpolation == 'CONSTANT':
                    shape = Shape.STEPPED
                elif pkf.interpolation == 'LINEAR':
                    shape = Shape.LINEAR
                else:
                    unsupported_occured.add(pkf.interpolation)
                    shape = replace_unsupported_to
            pkf = ckf
            yield KF(ckf.co.x / fps, ckf.co.y / kv, shape)

    cpw = PackedWriter()
    cnt = export_keyframes(cpw, refine_keys(generate_keys(fc.keyframe_points), epsilon))

    pw.putf('H', cnt)
    pw.putp(cpw)

    if len(unsupported_occured):
        warn('Envelope: unsupported shapes: {}, replaced by {}'.format(unsupported_occured, replace_unsupported_to.name))


def export_keyframes(cpw, keyframes):
    cnt = 0

    for kfrm in keyframes:
        cnt += 1
        cpw.putf('ff', kfrm.value, kfrm.time)
        cpw.putf('B', kfrm.shape.value)
        if kfrm.shape != Shape.STEPPED:
            cpw.putf('HHH', 32768, 32768, 32768)
            cpw.putf('HHHH', 32768, 32768, 32768, 32768)

    return cnt


def refine_keys(keyframes, epsilon=EPSILON):
    def significant(pkf, ckf, nkf, skipped):
        def is_oor(icf, nwk):
            ccy = (icf.time - pkf.time) * nwk + pkf.value
            return abs(ccy - icf.value) >= epsilon

        if pkf is None:
            return ckf is not None
        if (ckf.shape == Shape.LINEAR) and (nkf.shape == Shape.LINEAR):
            nwk = (nkf.value - pkf.value) / (nkf.time - pkf.time)
            if is_oor(ckf, nwk):
                return True
            for icf in skipped:
                if is_oor(icf, nwk):
                    return True
            return False
        if (abs(pkf.value - ckf.value) + abs(ckf.value - nkf.value)) < epsilon:
            return False
        return True

    pkf, ckf = None, None
    skipped = []
    for nkf in keyframes:
        if significant(pkf, ckf, nkf, skipped):
            skipped = []
            pkf = ckf
            yield ckf
        elif ckf is not None:
            skipped.append(ckf)
        ckf = nkf

    if ckf and ((not pkf) or (abs(ckf.value - pkf.value) >= epsilon)):
        yield ckf
