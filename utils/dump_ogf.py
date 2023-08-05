import os.path
import struct
import sys

for path in (
    '../io_scene_xray/rw',
    '../io_scene_xray/formats/ogf',
):
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), path)))

from read import ChunkedReader, PackedReader
from fmt import Chunks_v4 as Chunks, VertexFormat, HEADER
import io


def calc_hash(data):
    import hashlib

    m = hashlib.md5()
    m.update(data)
    return m.hexdigest()


def dump_ogf4_m03(cr, out, opts):
    dump_ogf4_m10(cr, out, opts)


def dump_ogf4_m04(cr, out, opts):
    dump_ogf4_m05(cr, out, opts)
    pr = PackedReader(cr.next(Chunks.SWIDATA))
    out('swidata: {')
    out('  ?:', pr.getf('IIII'))
    sc = pr.getf('I')[0]
    if opts.diff:
        out('  swis-info:', 'count=' + str(sc) + ', hash=' + calc_hash(pr.getb((4 + 2 + 2) * sc)))
    else:
        out('  swis: [')
        for _ in range(sc):
            out('    {offs: %i, tris: %i, vtxs: %i}' % pr.getf('IHH'))
        out('  ]')
    out('}')


def dump_ogf4_m05(cr, out, opts):
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
        if opts.diff:
            out('  data-info:', 'count=' + str(vc) + ', hash=' + calc_hash(pr.getb(15 * 4 * vc)))
        else:
            out('  data: [')
            for _ in range(vc):
                out('   {v: %s, n: %s, tg: %s, bn: %s, tx: %s, b: %i' % (
                    pr.getf('fff'), pr.getf('fff'), pr.getf('fff'), pr.getf('fff'), pr.getf('ff'), pr.getf('I')[0]))
            out('  ]')
    elif vf == VertexFormat.FVF_2L or vf == VertexFormat.FVF_2L_CS:
        out('  format:', 'fvf_2l' if vf == VertexFormat.FVF_2L else 'fvf_2l_cs')
        if opts.diff:
            out('  data-info:', 'count=' + str(vc) + ', hash=' + calc_hash(pr.getb(16 * 4 * vc)))
        else:
            out('  data: [')
            for _ in range(vc):
                out('   {b: %s, v: %s, n: %s, tg: %s, bn: %s, bw: %f, tx: %s' % (
                    pr.getf('HH'), pr.getf('fff'), pr.getf('fff'), pr.getf('fff'), pr.getf('fff'), pr.getf('f')[0], pr.getf('ff')))
            out('  ]')
    elif vf == VertexFormat.FVF_3L_CS or vf == VertexFormat.FVF_4L_CS:
        nl = 3 if vf == VertexFormat.FVF_3L_CS else 4
        out('  format:', 'fvf_' + str(nl) + 'l_cs')
        if opts.diff:
            out('  data-info:', 'count=' + str(vc) + ', hash=' + calc_hash(pr.getb(((14 + nl - 1) * 4 + nl * 2) * vc)))
        else:
            out('  data: [')
            for _ in range(vc):
                out('   {b: %s, v: %s, n: %s, tg: %s, bn: %s, bw: %s, tx: %s' % (
                    pr.getf(str(nl) + 'H'), pr.getf('fff'), pr.getf('fff'), pr.getf('fff'), pr.getf('fff'), pr.getf(str(nl - 1) + 'f'), pr.getf('ff')))
            out('  ]')
    else:
        raise Exception('unexpected vertex format: {:#x}'.format(vf))
    out('}')

    pr = PackedReader(cr.next(Chunks.INDICES))
    ic = pr.getf('I')[0] // 3
    if opts.diff:
        out('indices-info:', 'count=' + str(ic) + ', hash=' + calc_hash(pr.getb(3 * 2 * ic)))
    else:
        out('indices: {')
        for _ in range(ic):
            out(' ', pr.getf('HHH'))
        out('}')


def dump_ogf4_m10(cr, out, opts):
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
            try:
                out('  export tool:', pr.gets(onerror=print))
                out('  export time:', pr.getf('I')[0])
                out('  create tool:', pr.gets(onerror=print))
                out('  create time:', pr.getf('I')[0])
                out('  modify tool:', pr.gets(onerror=print))
                out('  modify time:', pr.getf('I')[0])
            except struct.error as e:
                print(e, bytes(pr.getv()))
            out('}')
        elif cid == Chunks.CHILDREN:
            out('children: [{')
            for _, ccr in ChunkedReader(data):
                if _: out('}, {')
                dump_ogf(ChunkedReader(ccr), oout, opts)
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
        elif cid == Chunks.S_IKDATA_2:
            out('s ikdata 2: [{')
            for _ in range(bonescount):
                if _: out('}, {')
                ver = pr.getf('I')[0]
                if ver != 0x1:
                    print('unexpected ikdata version: {:#x}'.format(ver))
                out('  version:', ver)
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
        elif cid == Chunks.S_MOTION_REFS_2:
            count = pr.getf('I')[0]
            out('s motion refs 2:', [pr.gets() for _ in range(count)])
        elif cid == Chunks.S_MOTIONS_0:
            out('s motions: len={}, hash={}'.format(len(data), calc_hash(data)))
        elif cid == Chunks.S_SMPARAMS_0:
            out('s smparams: {')
            ver = pr.getf('H')[0]
            if (ver != 3) and (ver != 4):
                print('unsupported smparams version={}'.format(ver))
            out('  version:', ver)
            out('  partitions: [{')
            for pi in range(pr.getf('H')[0]):
                if pi: out('  }, {')
                pn = pr.gets()
                out('    name:', pn)
                out('    bones: [{')
                for bi in range(pr.getf('H')[0]):
                    if bi: out('    }, {')
                    out('      name:', pr.gets())
                    out('      id:', pr.getf('I')[0])
                out('    }]')
                break
            out('  }]')
            out('}')
        else:
            print('unknown ogf4_m10 chunk={}({:#x}), len={}, hash={}'.format(cid, cid, len(data), calc_hash(data)))


def dump_ogf4(pr, cr, out, opts):
    model_type = pr.getf('B')[0]
    out('model type:', model_type)
    out('shader id:', pr.getf('H')[0])
    out('bounding box:', pr.getf('ffffff'))
    out('bounding sphere:', pr.getf('ffff'))
    if model_type == 3:
        dump_ogf4_m03(cr, out, opts)
    elif model_type == 4:
        dump_ogf4_m04(cr, out, opts)
    elif model_type == 5:
        dump_ogf4_m05(cr, out, opts)
    elif model_type == 10:
        dump_ogf4_m10(cr, out, opts)
    else:
        raise Exception('unsupported OGF model type: %i' % model_type)


def dump_ogf(cr, out, opts):
    pr = PackedReader(cr.next(HEADER))
    ver = pr.getf('B')[0]
    out('version:', ver)
    if ver == 4:
        dump_ogf4(pr, cr, out, opts)
    else:
        raise Exception('unsupported OGF format version: %i' % ver)


def main():
    from optparse import OptionParser
    parser = OptionParser(usage='Usage: dump_ogf.py <.ogf-file> [options]')
    parser.add_option("-d", "--diff", action='store_true', default=False, help='generate diff-ready dump')
    (options, args) = parser.parse_args()
    if not args:
        parser.print_help()
        sys.exit(2)
    with io.open(sys.argv[1], mode='rb') as f:
        dump_ogf(ChunkedReader(f.read()), print, options)


if __name__ == "__main__":
    main()
