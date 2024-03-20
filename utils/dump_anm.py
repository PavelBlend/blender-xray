import os
import sys
import optparse
import xray_io


MAIN_CHUNK = 0x1100


def dump_envelopes(packed_reader, version):

    for curve_index in range(6):

        if version > 3:
            behaviour_1 = packed_reader.getf('<B')[0]
            behaviour_2 = packed_reader.getf('<B')[0]
        else:
            behaviour_1 = packed_reader.getf('<I')[0]
            behaviour_2 = packed_reader.getf('<I')[0]

        print('    behaviour_1: {}'.format(behaviour_1))
        print('    behaviour_2: {}'.format(behaviour_2))

        if version > 3:
            frames_count = packed_reader.getf('<H')[0]
        else:
            frames_count = packed_reader.getf('<I')[0]

        print('    frames_count: {}'.format(frames_count))

        for frame_index in range(frames_count):
            print('        frame: {}'.format(frame_index))

            value = packed_reader.getf('<f')[0]
            time = packed_reader.getf('<f')[0]

            print('            value: {}'.format(value))
            print('            time: {}'.format(time))

            if version > 3:
                shape = packed_reader.getf('B')[0]

                print('            shape: {}'.format(shape))

                if shape != 4:
                    tension = packed_reader.getf('<H')[0]
                    continuity = packed_reader.getf('<H')[0]
                    bias = packed_reader.getf('<H')[0]
                    param_1 = packed_reader.getf('<H')[0]
                    param_2 = packed_reader.getf('<H')[0]
                    param_3 = packed_reader.getf('<H')[0]
                    param_4 = packed_reader.getf('<H')[0]

                    print('            tension: {}'.format(tension))
                    print('            continuity: {}'.format(continuity))
                    print('            bias: {}'.format(bias))
                    print('            param_1: {}'.format(param_1))
                    print('            param_2: {}'.format(param_2))
                    print('            param_3: {}'.format(param_3))
                    print('            param_4: {}'.format(param_4))

            else:
                shape = packed_reader.getf('H')[0]

                print('            shape: {}'.format(shape))

                if shape != 4:
                    tension = packed_reader.getf('<f')[0]
                    continuity = packed_reader.getf('<f')[0]
                    bias = packed_reader.getf('<f')[0]
                    param_1 = packed_reader.getf('<f')[0]
                    param_2 = packed_reader.getf('<f')[0]
                    param_3 = packed_reader.getf('<f')[0]
                    param_4 = packed_reader.getf('<f')[0]

                    print('            tension: {}'.format(tension))
                    print('            continuity: {}'.format(continuity))
                    print('            bias: {}'.format(bias))
                    print('            param_1: {}'.format(param_1))
                    print('            param_2: {}'.format(param_2))
                    print('            param_3: {}'.format(param_3))
                    print('            param_4: {}'.format(param_4))


def dump_anm(chunks):
    for chunk_id, chunk_data in chunks:

        if chunk_id != MAIN_CHUNK:
            print('UNKNOWN ANM CHUNK: {:#x}'.format(chunk_id))
            continue

        packed_reader = xray_io.PackedReader(chunk_data)

        name = packed_reader.gets()
        frame_start = packed_reader.getf('<I')[0]
        frame_end = packed_reader.getf('<I')[0]
        fps = packed_reader.getf('<f')[0]
        version = packed_reader.getf('<H')[0]

        if version not in (3, 4, 5):
            raise Exception('unsupported anm version: {}'.format(version))

        print('name: {}'.format(name))
        print('frame_start: {}'.format(frame_start))
        print('frame_end: {}'.format(frame_end))
        print('fps: {}'.format(fps))
        print('version: {}'.format(version))

        dump_envelopes(packed_reader, version)


def main():
    parser = optparse.OptionParser(
        usage='Usage: dump_anm.py <.anm-file> [options]'
    )
    options, args = parser.parse_args()

    if not args:
        parser.print_help()
        sys.exit(2)

    file_name = sys.argv[1]

    with open(file_name, mode='rb') as file:
        file_data = file.read()
        chunked_reader = xray_io.ChunkedReader(file_data)
        chunks = chunked_reader.read()
        dump_anm(chunks)


if __name__ == '__main__':
    main()
