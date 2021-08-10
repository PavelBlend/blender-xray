import os.path
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from io_scene_xray.xray_io import ChunkedReader, PackedReader
from io_scene_xray.anm.fmt import Chunks
import io


def dump_envelopes(pr, out):
    for i in range(6):
        if i: out('}, {')
        out('  behaviours:', pr.getf('BB'))
        out('  keys: [{')
        for j in range(pr.getf('H')[0]):
            if j: out('  }, {')
            out('    value:', pr.getf('f')[0])
            out('    time:', pr.getf('f')[0])
            shape = pr.getf('B')[0]
            out('    shape:', shape)
            if shape != 4:
                def rfq16(pr, mn, mx):
                    return pr.getf('H')[0] * (mx - mn) / 65536 + mn

                out('    tension:', rfq16(pr, -32, 32))
                out('    continuity:', rfq16(pr, -32, 32))
                out('    bias:', rfq16(pr, -32, 32))
                out('    params:', [rfq16(pr, -32, 32) for _4 in range(4)])
        out('  }]')


def dump_anm(cr, out, opts):
    for (cid, data) in cr:
        if cid != Chunks.MAIN:
            out('UNKNOWN ANM CHUNK: {:#x}'.format(cid))
            continue
        pr = PackedReader(data)
        out('name:', pr.gets())
        out('range:', pr.getf('II'))
        out('fps:', pr.getf('f')[0])
        ver = pr.getf('H')[0]
        if ver != 5:
            raise Exception('unsupported anm version: {}'.format(ver))
        out('version:', ver)
        out('envelopes: [{')
        dump_envelopes(pr, out)
        out('}]')


def main():
    from optparse import OptionParser
    parser = OptionParser(usage='Usage: dump_anm.py <.anm-file> [options]')
    (options, args) = parser.parse_args()
    if not args:
        parser.print_help()
        sys.exit(2)
    with io.open(sys.argv[1], mode='rb') as f:
        dump_anm(ChunkedReader(f.read()), print, options)


if __name__ == "__main__":
    main()
