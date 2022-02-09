import os
import sys
import optparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from io_scene_xray.xray_io import ChunkedReader, PackedReader


MOTIONS = 0xe
SMPARAMS = 0xf

SPACES = ' ' * 4


def dump_motions(chunk_id, data, out):
    out(' ! - Motions Chunk not Parsed')


def dump_params(chunk_id, data, out):
    out('Params Chunk:', hex(chunk_id), len(data))
    packed_reader = PackedReader(data)
    params_version = packed_reader.getf('<H')[0]
    out(SPACES * 1 + 'params version:', params_version)
    # bone parts
    partition_count = packed_reader.getf('<H')[0]
    out(SPACES * 1 + 'bone parts:')
    for partition_index in range(partition_count):
        partition_name = packed_reader.gets()
        out(
            SPACES * 2 + 'bone part {0}:'.format(partition_index),
            partition_name
        )
        bone_count = packed_reader.getf('<H')[0]
        out(
            SPACES * 3 + 'bones count:',
            bone_count
        )
        for bone in range(bone_count):
            out(
                SPACES * 4 + 'bone index:',
                bone
            )
            if params_version == 1:
                bone_id = packed_reader.getf('<I')[0]
                out(
                    SPACES * 5 + 'bone id:',
                    bone_id
                )
            elif params_version == 2:
                bone_name = packed_reader.gets()
                out(
                    SPACES * 5 + 'bone_name:',
                    bone_name
                )
            elif params_version == 3 or params_version == 4:
                bone_name = packed_reader.gets()
                bone_id = packed_reader.getf('<I')[0]
                out(
                    SPACES * 5 + 'bone_name:',
                    bone_name
                )
                out(
                    SPACES * 5 + 'bone id:',
                    bone_id
                )
            else:
                raise BaseException('Unknown params version')
    # motions params
    out(SPACES * 1 + 'motion params:')
    motion_count = packed_reader.getf('<H')[0]
    out(
        SPACES * 2 + 'motion count:',
        motion_count
    )
    for motion_index in range(motion_count):
        out(
            SPACES * 3 + 'motion index:',
            motion_index
        )
        name = packed_reader.gets()
        out(
            SPACES * 4 + 'name:',
            name
        )
        flags = packed_reader.getf('<I')[0]
        out(
            SPACES * 4 + 'flags:',
            flags
        )
        bone_or_part = packed_reader.getf('<H')[0]
        out(
            SPACES * 4 + 'bone or part:',
            bone_or_part
        )
        motion = packed_reader.getf('<H')[0]
        out(
            SPACES * 4 + 'motion:',
            motion
        )
        speed = packed_reader.getf('<f')[0]
        out(
            SPACES * 4 + 'speed:',
            speed
        )
        power = packed_reader.getf('<f')[0]
        out(
            SPACES * 4 + 'power:',
            power
        )
        accrue = packed_reader.getf('<f')[0]
        out(
            SPACES * 4 + 'accrue:',
            accrue
        )
        falloff = packed_reader.getf('<f')[0]
        out(
            SPACES * 4 + 'falloff:',
            falloff
        )
        if params_version == 4:
            # motion marks
            num_marks = packed_reader.getf('<I')[0]
            out(
                SPACES * 4 + 'marks count:',
                num_marks
            )
            for mark_index in range(num_marks):
                out(
                    SPACES * 5 + 'mark index:',
                    mark_index
                )
                mark_name = packed_reader.gets_a()
                out(
                    SPACES * 6 + 'mark name:',
                    mark_name
                )
                count = packed_reader.getf('<I')[0]
                out(
                    SPACES * 6 + 'intervals count:',
                    count
                )
                for index in range(count):
                    out(
                        SPACES * 7 + 'interval index:',
                        index
                    )
                    interval_first = packed_reader.getf('<f')[0]
                    out(
                        SPACES * 8 + 'interval first:',
                        interval_first
                    )
                    interval_second = packed_reader.getf('<f')[0]
                    out(
                        SPACES * 8 + 'interval second:',
                        interval_second
                    )


def dump_omf(chunked_reader, out, opts):
    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == MOTIONS:
            dump_motions(chunk_id, chunk_data, out)
        elif chunk_id == SMPARAMS:
            dump_params(chunk_id, chunk_data, out)
        else:
            out('UNKNOWN CHUNK:', hex(chunk_id), len(chunk_data))


def main():
    parser = optparse.OptionParser(
        usage='Usage: dump_omf.py <.omf-file> [options]'
    )
    (options, args) = parser.parse_args()
    if not args:
        parser.print_help()
        input('press enter...')
        sys.exit(2)
    with open(sys.argv[1], mode='rb') as file:
        data = file.read()
        reader = ChunkedReader(data)
        dump_omf(reader, print, options)


if __name__ == "__main__":
    main()
