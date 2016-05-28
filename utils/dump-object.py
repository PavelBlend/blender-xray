import os.path
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from io_scene_xray.xray_io import ChunkedReader, PackedReader
from io_scene_xray.fmt_object import Chunks
import io
import time


def calc_hash(data):
    import hashlib

    m = hashlib.md5()
    m.update(data)
    return m.hexdigest()


def dump_mesh(cr, out, opts):
    ver = cr.nextf(Chunks.Mesh.VERSION, 'H')[0]
    if ver != 0x11:
        raise Exception('unsupported MESH format version: {}'.format(ver))
    out('version:', ver)
    for (cid, data) in cr:
        pr = PackedReader(data)
        if cid == Chunks.Mesh.MESHNAME:
            out('meshname:', pr.gets())
        elif cid == Chunks.Mesh.BBOX:
            out('bbox:', pr.getf('fff'), '-', pr.getf('fff'))
        elif cid == Chunks.Mesh.FLAGS:
            out('flags:', pr.getf('B')[0])
        elif cid == Chunks.Mesh.OPTIONS:
            out('options:', pr.getf('II'))
        elif cid == Chunks.Mesh.VERTS:
            vc = pr.getf('I')[0]
            if opts.diff:
                out('vertices-info:', 'count=' + str(vc) + ', hash=' + calc_hash(data))
                continue
            out('vertices: [')
            for _ in range(vc):
                out(' ', pr.getf('fff'))
            out(']')
        elif cid == Chunks.Mesh.FACES:
            if opts.diff:
                out('faces-info:', 'count=' + str(pr.getf('I')[0]) + ', hash=' + calc_hash(data))
                continue
            out('faces: [')
            for _ in range(pr.getf('I')[0]):
                fr = pr.getf('IIIIII')
                f = ((fr[0], fr[2], fr[4]), (fr[1], fr[3], fr[5]))
                out(' ', f)
            out(']')
        elif cid == Chunks.Mesh.SG:
            if opts.diff:
                out('sgroups-hash:', calc_hash(data))
                continue
            out('sgroups:', [pr.getf('I')[0] for _ in range(len(data) // 4)])
        elif cid == Chunks.Mesh.VMREFS:
            if opts.diff:
                out('vmrefs-hash:', calc_hash(data))
                continue
            out('vmrefs: [')
            for _ in range(pr.getf('I')[0]):
                sz = pr.getf('B')[0]
                out(' ', [pr.getf('II') for __ in range(sz)])
            out(']')
        elif cid == Chunks.Mesh.SFACE:
            out('sfaces: [{')
            for _ in range(pr.getf('H')[0]):
                if _: out('}, {')
                out('  name:', pr.gets())
                sz = pr.getf('I')[0]
                if opts.diff:
                    out('  faces-info:', 'count=' + str(sz) + ', hash=' + calc_hash(pr.getb(sz * 4)))
                    continue
                out('  faces:', [pr.getf('I')[0] for __ in range(sz)])
            out('}]')
        elif cid == Chunks.Mesh.VMAPS0:
            out('vmaps0: [{')
            for _ in range(pr.getf('I')[0]):
                if _: out('}, {')
                out('  name:', pr.gets())
                sz = pr.getf('I')[0]
                if opts.diff:
                    out('  uvs-hash:', calc_hash(pr.getb(sz * 2 * 4)))
                    out('  vtx-hash:', calc_hash(pr.getb(sz * 1 * 4)))
                    continue
                out('  uvs:', [pr.getf('ff') for __ in range(sz)])
                out('  vtx:', [pr.getf('I')[0] for __ in range(sz)])
            out('}]')
        elif cid == Chunks.Mesh.VMAPS2:
            out('vmaps2: [{')
            for _ in range(pr.getf('I')[0]):
                if _: out('}, {')
                out('  name:', pr.gets())
                out('  dim:', pr.getf('B')[0] & 0x3)
                dsc = pr.getf('B')[0] & 0x1
                out('  dsc:', dsc)
                typ = pr.getf('B')[0] & 0x3  # enum {VMT_UV,VMT_WEIGHT}
                out('  type:', typ)
                sz = pr.getf('I')[0]
                if opts.diff:
                    if typ == 0:
                        out('  uvs-hash:', calc_hash(pr.getb(sz * 2 * 4)))
                    elif typ == 1:
                        out('  wgh-hash:', calc_hash(pr.getb(sz * 4)))
                    out('  vtx-hash:', calc_hash(pr.getb(sz * 4)))
                    if dsc != 0:
                        out('  fcs-hash:', calc_hash(pr.getb(sz * 4)))
                    continue
                if typ == 0:
                    out('  uvs:', [pr.getf('ff') for __ in range(sz)])
                elif typ == 1:
                    out('  wgh:', [pr.getf('f')[0] for __ in range(sz)])
                out('  vtx:', [pr.getf('I')[0] for __ in range(sz)])
                if dsc != 0:
                    out('  fcs:', [pr.getf('I')[0] for __ in range(sz)])
            out('}]')
        else:
            out('UNKNOWN MESH CHUNK: {:#x}'.format(cid))


def dump_bone(cr, out):
    ver = cr.nextf(Chunks.Bone.VERSION, 'H')[0]
    if ver != 0x2:
        raise Exception('unsupported BONE format version: {}'.format(ver))
    pr = PackedReader(cr.next(Chunks.Bone.DEF))
    out('def: {')
    out('  name:', pr.gets())
    out('  parent:', pr.gets())
    out('  vmap:', pr.gets())
    out('}')
    for (cid, data) in cr:
        pr = PackedReader(data)
        if cid == Chunks.Bone.BIND_POSE:
            out('pose: {')
            out('  offset:', pr.getf('fff'))
            out('  rotate:', pr.getf('fff'))
            out('  length:', pr.getf('f')[0])
            out('}')
        elif cid == Chunks.Bone.DEF:
            out('def:', pr.gets())
        elif cid == Chunks.Bone.MATERIAL:
            out('gamemtl:', pr.gets())
        elif cid == Chunks.Bone.SHAPE:
            out('shape: {')
            out('  type:', pr.getf('H')[0])
            out('  flags:', pr.getf('H')[0])
            out('  box: rot={}, tr={}, hs={}'.format(pr.getf('fffffffff'), pr.getf('fff'), pr.getf('fff')))
            out('  sphere: pos={}, rad={}'.format(pr.getf('fff'), pr.getf('f')[0]))
            out('  cylinder: ctr={}, dir={}, h={}, r={}'.format(pr.getf('fff'), pr.getf('fff'), pr.getf('f')[0], pr.getf('f')[0]))
            out('}')
        elif cid == Chunks.Bone.IK_FLAGS:
            out('ik_flags:', pr.getf('I')[0])
        elif cid == Chunks.Bone.IK_JOINT:
            out('ik_joint: {')
            out('  type:', pr.getf('I')[0])
            out('  lims: {}, spr={}, dmp={}'.format(pr.getf('fff'), pr.getf('f')[0], pr.getf('f')[0]))
            out('  spring:', pr.getf('f')[0])
            out('  damping:', pr.getf('f')[0])
            out('}')
        elif cid == Chunks.Bone.BREAK_PARAMS:
            out('break: {')
            out('  force:', pr.getf('f')[0])
            out('  torque:', pr.getf('f')[0])
            out('}')
        elif cid == Chunks.Bone.FRICTION:
            out('friction:', pr.getf('f')[0])
        elif cid == Chunks.Bone.MASS_PARAMS:
            out('mass: {')
            out('  value:', pr.getf('f')[0])
            out('  center:', pr.getf('fff'))
            out('}')
        else:
            out('UNKNOWN BONE CHUNK: {:#x}'.format(cid))


def dump_object(cr, out, opts):
    def oout(*args):
        out(' ', *args)

    cr = ChunkedReader(cr.next(Chunks.Object.MAIN))
    ver = cr.nextf(Chunks.Object.VERSION, 'H')[0]
    if ver != 0x10:
        raise Exception('unsupported OBJECT format version: {}'.format(ver))
    out('version:', ver)

    getserr = ''

    def gets_error(e):
        global getserr
        getserr = ' //!' + str(e)

    def sgets(pr):
        global getserr
        getserr = ''
        return pr.gets(onerror=gets_error) + getserr

    for (cid, data) in cr:
        pr = PackedReader(data)
        if cid == Chunks.Object.USERDATA:
            out('userdata:', sgets(pr))
        elif cid == Chunks.Object.LOD_REF:
            out('lod_ref:', pr.gets())
        elif cid == Chunks.Object.FLAGS:
            out('flags:', pr.getf('I')[0])
        elif cid == Chunks.Object.MESHES:
            out('meshes: [{')
            for (_, d) in ChunkedReader(data):
                if _: out('}, {')
                dump_mesh(ChunkedReader(d), oout, opts)
            out('}]')
        elif (cid == Chunks.Object.SURFACES1) or (cid == Chunks.Object.SURFACES2):
            out('surfaces{}'.format(cid - Chunks.Object.SURFACES1 + 1) + ': [{')
            for _ in range(pr.getf('I')[0]):
                if _: out('}, {')
                out('  name:', pr.gets())
                out('  eshader:', pr.gets())
                out('  cshader:', pr.gets())
                if cid == Chunks.Object.SURFACES2:
                    out('  gamemtl:', pr.gets())
                out('  texture:', pr.gets())
                out('  vmap:', pr.gets())
                out('  flags:', pr.getf('I')[0])
                fvf = pr.getf('I')[0]
                out('  fvf:', 'default' if fvf == 0x112 else fvf)
                out('  ?=1:', pr.getf('I')[0])
            out('}]')
        elif cid == Chunks.Object.BONES:
            out('bones: [{')
            pr = PackedReader(data)
            for _ in range(pr.getf('I')[0]):
                if _: out('}, {')
                out('  def: {')
                out('    name:', pr.gets())
                out('    parent:', pr.gets())
                out('    vmap:', pr.gets())
                out('  }')
                out('  pose: {')
                out('    offset:', pr.getf('fff'))
                out('    rotate:', pr.getf('fff'))
                out('    length:', pr.getf('f')[0])
                out('  }')
            out('}]')
        elif cid == Chunks.Object.BONES1:
            out('bones: [{')
            for (_, d) in ChunkedReader(data):
                if _: out('}, {')
                dump_bone(ChunkedReader(d), oout)
            out('}]')
        elif cid == Chunks.Object.TRANSFORM:
            out('transform: {')
            out('  position:', pr.getf('fff'))
            out('  rotation:', pr.getf('fff'))
            out('}')
        elif cid == Chunks.Object.PARTITIONS0:
            out('partitions1: [{')
            for _ in range(pr.getf('I')[0]):
                if _: out('}, {')
                out('  name:', pr.gets())
                sz = pr.getf('I')[0]
                out('  bones:', pr.getf('%dI' % sz))
            out('}]')
        elif cid == Chunks.Object.PARTITIONS1:
            out('partitions1: [{')
            for _ in range(pr.getf('I')[0]):
                if _: out('}, {')
                out('  name:', pr.gets())
                sz = pr.getf('I')[0]
                out('  bones:', [pr.gets() for __ in range(sz)])
            out('}]')
        elif cid == Chunks.Object.MOTION_REFS:
            out('motion_refs:', pr.gets())
        elif cid == Chunks.Object.REVISION:
            out('revision: {')
            out('  owner:', pr.gets())
            out('  ctime:', time.ctime(pr.getf('I')[0]))
            out('  moder:', pr.gets())
            out('  mtime:', time.ctime(pr.getf('I')[0]))
            out('}')
        elif cid == Chunks.Object.MOTIONS:
            if opts.diff:
                out('motions-info:', 'count=' + str(pr.getf('I')[0]) + ', hash=' + calc_hash(data))
                continue
            out('motions: [{')
            for _ in range(pr.getf('I')[0]):
                if _: out('}, {')
                out('  name:', pr.gets())
                out('  range:', pr.getf('II'))
                out('  fps:', pr.getf('f')[0])
                ver = pr.getf('H')[0]
                out('  version:', ver)
                out('  flags:', pr.getf('B')[0])
                out('  bone_or_part:', pr.getf('H')[0])
                out('  speed:', pr.getf('f')[0])
                out('  accrue:', pr.getf('f')[0])
                out('  falloff:', pr.getf('f')[0])
                out('  power:', pr.getf('f')[0])
                oout('bone_motions: [{')
                for _1 in range(pr.getf('H')[0]):
                    if _1: oout('}, {')
                    oout('  bone:', pr.gets())
                    oout('  flags:', pr.getf('B')[0])
                    oout('  envelopes: [{')
                    for _2 in range(6):
                        if _2: oout('  }, {')
                        oout('    behaviours:', pr.getf('BB'))
                        oout('    keys: [{')
                        for _3 in range(pr.getf('H')[0]):
                            if _3: oout('    }, {')
                            oout('      value:', pr.getf('f')[0])
                            oout('      time:', pr.getf('f')[0])
                            shape = pr.getf('B')[0]
                            oout('      shape:', shape)
                            if shape != 4:
                                def rfq16(pr, mn, mx):
                                    return pr.getf('H')[0] * (mx - mn) / 65536 + mn
                                oout('      tension:', rfq16(pr, -32, 32))
                                oout('      continuity:', rfq16(pr, -32, 32))
                                oout('      bias:', rfq16(pr, -32, 32))
                                oout('      params:', [rfq16(pr, -32, 32) for _4 in range(4)])
                        oout('    }]')
                    oout('  }]')
                oout('}]')
            out('}]')
        elif cid == Chunks.Object.SMOTIONS3:
            out('smotions3:', [pr.gets() for _ in range(pr.getf('I')[0])])
        elif cid == Chunks.Object.LIB_VERSION:
            out('lib_version:', pr.getf('Q')[0])
        else:
            out('UNKNOWN OBJ CHUNK: {:#x}'.format(cid))


def main():
    from optparse import OptionParser
    parser = OptionParser(usage='Usage: dump-object.py <.object-file> [options]')
    parser.add_option("-d", "--diff", action='store_true', default=False, help='generate diff-ready dump')
    (options, args) = parser.parse_args()
    if not args:
        parser.print_help()
        sys.exit(2)
    with io.open(sys.argv[1], mode='rb') as f:
        dump_object(ChunkedReader(f.read()), print, options)


if __name__ == "__main__":
    main()
