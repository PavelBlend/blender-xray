import sys
import os
from optparse import OptionParser


utils_dir = os.path.dirname(os.path.abspath(__file__))
repo_path = os.path.dirname(utils_dir)
sys.path.append(repo_path)


from io_scene_xray import xray_io


def decompress_chunks(data):
    chunked_reader = xray_io.ChunkedReader(data)
    chunked_writer = xray_io.ChunkedWriter()
    for chunk_id, chunk_data in chunked_reader:
        # bad file
        if chunk_id == 0x0 and len(chunk_data) == 0:
            break
        packed_writer = xray_io.PackedWriter()
        packed_writer.data = chunk_data
        chunked_writer.put(chunk_id, packed_writer)
        print('saved chunk: 0x{:x}'.format(chunk_id))
    with open(sys.argv[1] + '.decompressed', mode='wb') as file:
        file.write(chunked_writer.data)


def main():
    parser = OptionParser(usage='Usage: decompress_chunks.py <file>')
    (options, args) = parser.parse_args()
    if not args:
        parser.print_help()
        sys.exit(2)
    with open(sys.argv[1], mode='rb') as file:
        data = file.read()
        decompress_chunks(data)


if __name__ == '__main__':
    main()
