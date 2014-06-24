import os.path
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from io_scene_xray.xray_io import ChunkedReader, PackedReader
from io_scene_xray.fmt_ogf import Chunks, VertexFormat
import io


def dump_ogf4_m03(cr, out):
    dump_ogf4_m10(cr, out)


def dump_ogf4_m04(cr, out):
    dump_ogf4_m05(cr, out)
    pr = PackedReader(cr.next(Chunks.SWIDATA))
    out('swidata: {')
    out('  ?:', pr.getf('IIII'))
    out('  swis: [')
    for _ in range(pr.getf('I')[0]):
        out('    {offs: %i, tris: %i, vtxs: %i}' % pr.getf('IHH'))
    out('  ]')
    out('}')


def dump_ogf4_m05(cr, out):
    pr = PackedReader(cr.next(Chunks.TEXTURE))
    out('texture: {')
    out('  image:', pr.gets())
    out('  shader:', pr.gets())
    out('}')

    pr = PackedReader(cr.next(Chunks.VERTICES))
    out('vertices: {')
    vf, vc = pr.getf('II')
    if vf == VertexFormat.FVF_1L or vf == VertexFormat.FVF_1L_CS:
        out('  format:', 'fvf_2l' if vf == VertexFormat.FVF_1L else 'fvf_1l_cs')
        out('  data: [')
        for _ in range(vc):
            out('   {v: %s, n: %s, tg: %s, bn: %s, tx: %s, b: %i' % (
                pr.getf('fff'), pr.getf('fff'), pr.getf('fff'), pr.getf('fff'), pr.getf('ff'), pr.getf('I')[0]))
        out('  ]')
    elif vf == VertexFormat.FVF_2L or vf == VertexFormat.FVF_2L_CS:
        out('  format:', 'fvf_2l' if vf == VertexFormat.FVF_2L else 'fvf_2l_cs')
        out('  data: [')
        for _ in range(vc):
            out('   {b: %s, v: %s, n: %s, tg: %s, bn: %s, bw: %f, tx: %s' % (
                pr.getf('HH'), pr.getf('fff'), pr.getf('fff'), pr.getf('fff'), pr.getf('fff'), pr.getf('f')[0], pr.getf('ff')))
        out('  ]')
    else:
        raise Exception('unexpected vertex format: {:#x}'.format(vf))
    out('}')

    pr = PackedReader(cr.next(Chunks.INDICES))
    out('indices: {')
    for _ in range(pr.getf('I')[0] // 3):
        out(' ', pr.getf('HHH'))
    out('}')


def dump_ogf4_m10(cr, out):
    def oout(*args):
        out(' ', *args)

    def ooout(*args):
        oout(' ', *args)

    def dump_box(pr, out):
        out('box: {')
        out('  rotation:', pr.getf('fffffffff'))
        out('  position:', pr.getf('fff'))
        out('  halfsize:', pr.getf('fff'))
        out('}')

    bonescount = 0
    for cid, data in cr:
        pr = PackedReader(data)
        if cid == Chunks.S_DESC:
            out('s desc: {')
            out('  src:', pr.gets())
            out('  export tool:', pr.gets())
            out('  export time:', pr.getf('I')[0])
            out('  create time:', pr.getf('I')[0])
            out('  modify time:', pr.getf('I')[0])
            out('}')
        elif cid == Chunks.CHILDREN:
            out('children: [{')
            for _, ccr in ChunkedReader(data):
                if _: out('}, {')
                dump_ogf(ChunkedReader(ccr), oout)
            out('}]')
        elif cid == Chunks.S_USERDATA:
            out('userdata:', pr.gets())
        elif cid == Chunks.S_BONE_NAMES:
            out('s bone names: [{')
            bonescount = pr.getf('I')[0]
            for _ in range(bonescount):
                if _: out('}, {')
                out('  name:', pr.gets())
                out('  parent:', pr.gets())
                dump_box(pr, oout)
            out('}]')
        elif cid == Chunks.S_IKDATA:
            out('s ikdata: [{')
            for _ in range(bonescount):
                if _: out('}, {')
                ver = pr.getf('I')[0]
                if ver != 0x1:
                    raise Exception('unexpected ikdata version: {:#x}'.format(ver))
                out('  gamemtl:', pr.gets())
                out('  shape: {')
                out('    type:', pr.getf('H')[0])
                out('    flags:', pr.getf('H')[0])
                dump_box(pr, ooout)
                out('    sphere: {')
                out('      center:', pr.getf('fff'))
                out('      radius:', pr.getf('f')[0])
                out('    }')
                out('    cylinder: {')
                out('      center:', pr.getf('fff'))
                out('      direction:', pr.getf('fff'))
                out('      height:', pr.getf('f')[0])
                out('      radius:', pr.getf('f')[0])
                out('    }')
                out('  }')
                out('  joint: {')
                out('    type:', pr.getf('I')[0])
                out('    limits: [')
                out('      {%s, s: %f, d: %f}' % (pr.getf('ff'), pr.getf('f')[0], pr.getf('f')[0]))
                out('      {%s, s: %f, d: %f}' % (pr.getf('ff'), pr.getf('f')[0], pr.getf('f')[0]))
                out('      {%s, s: %f, d: %f}' % (pr.getf('ff'), pr.getf('f')[0], pr.getf('f')[0]))
                out('    ]')
                out('    spring:', pr.getf('f')[0])
                out('    damping:', pr.getf('f')[0])
                out('    flags:', pr.getf('I')[0])
                out('    break: {')
                out('      force:', pr.getf('f')[0])
                out('      torque:', pr.getf('f')[0])
                out('    }')
                out('    friction:', pr.getf('f')[0])
                out('  }')
                out('  rotation:', pr.getf('fff'))
                out('  position:', pr.getf('fff'))
                out('  mass: {')
                out('    value:', pr.getf('f')[0])
                out('    center:', pr.getf('fff'))
                out('  }')
            out('}]')
        elif cid == Chunks.S_MOTION_REFS_0:
            out('s motion refs 0:', pr.gets())
        else:
            print('unknown ogf4_m10 chunk={:#x}'.format(cid))


def dump_ogf4(pr, cr, out):
    model_type = pr.getf('B')[0]
    out('model type:', model_type)
    out('shader id:', pr.getf('H')[0])
    out('bounding box:', pr.getf('ffffff'))
    out('bounding sphere:', pr.getf('ffff'))
    if model_type == 3:
        dump_ogf4_m03(cr, out)
    elif model_type == 4:
        dump_ogf4_m04(cr, out)
    elif model_type == 5:
        dump_ogf4_m05(cr, out)
    else:
        raise Exception('unsupported OGF model type: %i' % model_type)


def dump_ogf(cr, out):
    pr = PackedReader(cr.next(Chunks.HEADER))
    ver = pr.getf('B')[0]
    out('version:', ver)
    if ver == 4:
        dump_ogf4(pr, cr, out)
    else:
        raise Exception('unsupported OGF format version: %i' % ver)


if len(sys.argv) < 2:
    print('usage: dump-ogf.py <ogf-file>')
else:
    with io.open(sys.argv[1], mode='rb') as f:
        # with io.open('stalker_do_balon_4.ogf', mode='rb') as f:
        dump_ogf(ChunkedReader(f.read()), print)
