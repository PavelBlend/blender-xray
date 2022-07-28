import os
import sys
import optparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from io_scene_xray.xray_io import ChunkedReader, PackedReader


MOTIONS_0 = 0x1a
MOTIONS_1 = 0xe
SMPARAMS_0 = 0x14
SMPARAMS_1 = 0xf

FL_T_KEY_PRESENT = 1 << 0
FL_R_KEY_ABSENT = 1 << 1
KPF_T_HQ = 1 << 2

SPACES = ' ' * 4


def dump_motion(data, out, bones_count):
    packed_reader = PackedReader(data)
    name = packed_reader.gets()
    out(SPACES * 2 + 'name:', name)
    length = packed_reader.getf('<I')[0]
    out(SPACES * 2 + 'length:', length)
    out(SPACES * 2 + 'keyframes:')
    for bone_id in range(bones_count):
        out(SPACES * 3 + 'bone id:', bone_id)
        flags = packed_reader.getf('<B')[0]
        out(SPACES * 4 + 'flags:', flags)
        t_present = flags & FL_T_KEY_PRESENT
        r_absent = flags & FL_R_KEY_ABSENT
        hq = flags & KPF_T_HQ
        out(SPACES * 5 + 'translate present:', bool(t_present))
        out(SPACES * 5 + 'rotate absent:', bool(r_absent))
        out(SPACES * 5 + 'high quality:', bool(hq))
        # rotation
        out(SPACES * 4 + 'rotation:')
        if r_absent:
            quaternion = packed_reader.getf('<4h')
            out(SPACES * 5 + 'quaternions:')
            out(SPACES * 6 + 'quaternion:', quaternion)
        else:
            motion_crc32 = packed_reader.getf('<I')[0]
            out(SPACES * 5 + 'motion crc32:', motion_crc32)
            out(SPACES * 5 + 'quaternions:')
            for key_index in range(length):
                quaternion = packed_reader.getf('<4h')
                out(SPACES * 6 + 'quaternion:', quaternion)
        # translation
        out(SPACES * 4 + 'translation:')
        if t_present:
            motion_crc32 = packed_reader.getf('<I')[0]
            out(SPACES * 5 + 'motion crc32:', motion_crc32)
            if hq:
                translate_format = '<3h'
            else:
                translate_format = '<3b'
            out(SPACES * 5 + 'translations:')
            for key_index in range(length):
                translate = packed_reader.getf(translate_format)
                out(SPACES * 6 + 'translate:', translate)
            t_size = packed_reader.getf('<3f')
            t_init = packed_reader.getf('<3f')
            out(SPACES * 5 + 'translation size:', t_size)
            out(SPACES * 5 + 'translation init:', t_init)
        else:
            out(SPACES * 5 + 'translations:')
            translate = packed_reader.getf('<3f')
            out(SPACES * 6 + 'translate:', translate)


def dump_motions(chunk_id, data, out, bones_count):
    out('Motions Chunk:', hex(chunk_id), len(data))
    chunked_reader = ChunkedReader(data)
    for motion_id, chunk_data in chunked_reader:
        out(SPACES * 1 + 'chunk {0}: {1} bytes'.format(motion_id, len(chunk_data)))
        if motion_id == 0:
            packed_reader = PackedReader(chunk_data)
            motions_count = packed_reader.getf('<I')[0]
            out(SPACES * 2 + 'motions count:', motions_count)
        else:
            dump_motion(chunk_data, out, bones_count)


def dump_params(chunk_id, data, out):
    out('Params Chunk:', hex(chunk_id), len(data))
    packed_reader = PackedReader(data)
    params_version = packed_reader.getf('<H')[0]
    out(SPACES * 1 + 'params version:', params_version)
    # bone parts
    partition_count = packed_reader.getf('<H')[0]
    out(SPACES * 1 + 'partition count:', partition_count)
    out(SPACES * 1 + 'bone parts:')
    all_bones_count = 0
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
        all_bones_count += bone_count
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
    return all_bones_count


def dump_omf(chunked_reader, out, opts):
    chunks = {}
    for chunk_id, chunk_data in chunked_reader:
        chunks[chunk_id] = chunk_data

    chunk_data = chunks.pop(SMPARAMS_0, None)
    if chunk_data is None:
        chunk_data = chunks.pop(SMPARAMS_1)
    bones_count = dump_params(chunk_id, chunk_data, out)

    chunk_data = chunks.pop(MOTIONS_0, None)
    if chunk_data is None:
        chunk_data = chunks.pop(MOTIONS_1)
    dump_motions(chunk_id, chunk_data, out, bones_count)

    for chunk_id, chunk_data in chunks.items():
        out('UNKNOWN CHUNK:', hex(chunk_id), len(chunk_data))


def empty_print(*v, **kw):
    pass


def main():
    parser = optparse.OptionParser(
        usage='Usage: dump_omf.py <.omf-file> [options]'
    )
    parser.add_option(
        '-d',
        '--directory',
        nargs=0,
        dest='directory_mode',
        help=
            'Treat path as a folder. '
            'All files in the folder will be processed. '
            'Example: '
            '-d test_folder'
    )
    parser.add_option(
        '-r',
        '--recursive',
        nargs=1,
        dest='recursive_depth',
        type='int',
        help=
            'Use recursion. Read files from subfolders. '
            'The -r must be followed by an integer. '
            'This number will indicate the depth of the recursion. '
            'If this option is not specified, then the recursion '
            'will have no limits. '
            'Example: -r 5'
    )
    parser.add_option(
        '-i',
        '--invisible',
        dest='invisible',
        nargs=0,
        help='Do not print file data to console.'
    )
    (options, args) = parser.parse_args()
    if not args:
        parser.print_help()
        input('press enter...')
        sys.exit(2)
    is_dir = options.directory_mode
    invisible = options.invisible
    if invisible is None:
        print_function = print
    else:
        print_function = empty_print
    if is_dir is None:
        with open(sys.argv[1], mode='rb') as file:
            data = file.read()
            reader = ChunkedReader(data)
            dump_omf(reader, print_function, options)
    else:
        recursive_depth = options.recursive_depth
        if recursive_depth is None:
            recursive_depth = 1024
        root_folder = sys.argv[1]
        if not root_folder.endswith(os.sep):
            root_folder += os.sep
        for root, dirs, files in os.walk(root_folder):
            for file in files:
                ext = os.path.splitext(file)[-1].lower()
                if not ext == '.omf':
                    continue
                subfolders = root[len(root_folder) : ]
                if not subfolders:
                    folder_depth = 0
                else:
                    folder_depth = subfolders.count(os.sep) + 1
                file_path = os.path.abspath(os.path.join(root, file))
                if folder_depth > recursive_depth:
                    continue
                print(file_path, end='')
                with open(file_path, mode='rb') as file:
                    data = file.read()
                    reader = ChunkedReader(data)
                    try:
                        dump_omf(reader, print_function, options)
                        print()
                    except:
                        print(' ERROR')


if __name__ == "__main__":
    main()
