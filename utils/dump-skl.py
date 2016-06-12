import os.path
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import io
from io_scene_xray.xray_io import ChunkedReader, PackedReader

dump_object = __import__('dump-object')


def dump_skl(cr, out):
    for (cid, data) in cr:
        if cid != 0x1200:
            out('UNKNOWN CHUNK: {:#x}'.format(cid))
            continue
        pr = PackedReader(data)
        dump_object.dump_motion(pr, out)


def dump_skls(pr, out):
    def oout(*args):
        out(' ', *args)

    out('{')
    for _ in range(pr.getf('I')[0]):
        if _: out('}, {')
        dump_object.dump_motion(pr, oout)
    out('}')


def main():
    from optparse import OptionParser
    parser = OptionParser(usage='Usage: dump-skl.py <.skl|.skls-file>')
    (options, args) = parser.parse_args()
    if not args:
        parser.print_help()
        sys.exit(2)
    with io.open(args[0], mode='rb') as f:
        ext = os.path.splitext(args[0])[-1].lower()
        if ext == '.skl':
            dump_skl(ChunkedReader(f.read()), print)
        elif ext == '.skls':
            dump_skls(PackedReader(f.read()), print)
        else:
            raise Exception('unknown file type: ' + ext)


if __name__ == "__main__":
    main()
