from enum import Enum


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


def export_envelope(pw, fc, fps, kv, warn=print):
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
    fckf = fc.keyframe_points
    pw.putf('H', len(fckf))
    pkf = None
    for kf in fckf:
        pw.putf('ff', kf.co.y / kv, kf.co.x / fps)
        sh = Shape.STEPPED
        if pkf:
            if pkf.interpolation == 'CONSTANT':
                sh = Shape.STEPPED
            elif pkf.interpolation == 'LINEAR':
                sh = Shape.LINEAR
            else:
                unsupported_occured.add(pkf.interpolation)
                sh = replace_unsupported_to
        pw.putf('B', sh.value)
        if sh != Shape.STEPPED:
            pw.putf('HHH', 32768, 32768, 32768)
            pw.putf('HHHH', 32768, 32768, 32768, 32768)
        pkf = kf

    if len(unsupported_occured):
        warn('Envelope: unsupported shapes: {}, replaced by {}'.format(unsupported_occured, replace_unsupported_to.name))
