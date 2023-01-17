import os

from xray_io import PackedReader, ChunkedReader


class Chunks_v4:
    HEADER = 1
    TEXTURE = 2
    VERTICES = 3
    INDICES = 4
    SWIDATA = 6
    VCONTAINER = 7
    ICONTAINER = 8
    CHILDREN = 9
    CHILDREN_L = 10
    LODDEF2 = 11
    TREEDEF2 = 12
    S_BONE_NAMES = 13
    S_MOTIONS = 14
    S_SMPARAMS = 15
    S_IKDATA = 16
    S_USERDATA = 17
    S_DESC = 18
    S_MOTION_REFS_0 = 19
    SWICONTAINER = 20
    GCONTAINER = 21
    FASTPATH = 22
    S_LODS = 23
    S_MOTION_REFS_2 = 24


class Chunks_v3:
    HEADER = 1
    TEXTURE = 2
    MATERIAL = 4
    CHIELDS = 5
    BBOX = 6
    VERTICES = 7
    INDICES = 8
    P_MAP = 9
    VCONTAINER = 10
    BSPHERE = 11
    CHIELDS_L = 12
    BONE_NAMES = 13
    MOTIONS = 14
    DPATCH = 15
    P_LODS = 16
    CHILDREN = 17
    SMPARAMS = 18
    ICONTAINER = 19
    SMPARAMS2 = 20
    LODDEF2 = 21
    TREEDEF2 = 22
    IKDATA_obs = 23
    USERDATA = 24
    IKDATA = 25
    MOTIONS2 = 26
    DESC = 27
    IKDATA2 = 28
    MOTION_REFS = 29
    VERTICES2 = 30


class D3D9FVF:
    XYZ = 0x002    # x, y, z
    NORMAL = 0x010
    TEXCOUNT_SHIFT = 8


class VertFmt_v4:
    FVF_1L = 1 * 0x12071980
    FVF_2L = 2 * 0x12071980
    FVF_1L_CS = 1
    FVF_2L_CS = 2
    FVF_3L_CS = 3
    FVF_4L_CS = 4
    FVF_OGF = D3D9FVF.XYZ | D3D9FVF.NORMAL | (1 << D3D9FVF.TEXCOUNT_SHIFT)


# motion flags
FL_T_KEY_PRESENT = 1 << 0
FL_R_KEY_ABSENT = 1 << 1
KPF_T_HQ = 1 << 2

OGF_VERSION_3 = 3
OGF_VERSION_4 = 4
BONE_VERSION_0 = 0
BONE_VERSION_1 = 1
PARAMS_VERSION_1 = 1
PARAMS_VERSION_2 = 2
PARAMS_VERSION_3 = 3
PARAMS_VERSION_4 = 4


reader = None


def dump_smparams_1():
    partition_count = read('H', 'partition_count')

    for partition_index in range(partition_count):
        read('str', 'partition_name')
        bone_count = read('H', 'bone_count')

        for bone_index in range(bone_count):
            read('I', 'bone_id')

    motion_count = read('H', 'motion_count')
    for motion_index in range(motion_count):
        read('str', 'motion_name')
        read('B', 'b_cycle')
        read('H', 'bone_or_part')
        read('H', 'motion_id')
        read('f', 'speed')
        read('f', 'power')
        read('f', 'accrue')
        read('f', 'falloff')
        read('B', 'b_no_loop')


def dump_smparams_2():
    params_version = read('H', 'params_version')

    if not params_version in (PARAMS_VERSION_1, PARAMS_VERSION_2, PARAMS_VERSION_3, PARAMS_VERSION_4):
        raise 'Unsupported PARAMS format version!'

    partition_count = read('H', 'partition_count')

    for partition_index in range(partition_count):
        read('str', 'partition_name')
        bone_count = read('H', 'bone_count')

        if params_version in (PARAMS_VERSION_3, PARAMS_VERSION_4):
            for bone_index in range(bone_count):
                read('str', 'bone_name')
                read('I', 'bone_id')

        elif params_version == PARAMS_VERSION_2:
            for bone_index in range(bone_count):
                read('str', 'bone_name')

        elif params_version == PARAMS_VERSION_1:
            for bone_index in range(bone_count):
                read('I', 'bone_id')

    motion_count = read('H', 'motion_count')

    global reader

    for motion_index in range(motion_count):
        read('str', 'motion_name')
        read('I', 'flags')
        read('H', 'bone_or_part')
        read('H', 'motion_id')
        read('f', 'speed')
        read('f', 'power')
        read('f', 'accrue')
        read('f', 'falloff')

        if params_version == PARAMS_VERSION_4:
            marks_count = read('I', 'marks_count')
            reader.str_end = 0xa
            for mark_index in range(marks_count):
                read('str', 'marks_name')
                count = read('I', 'count')
                for index in range(count):
                    read('f', 'interval_first')
                    read('f', 'interval_second')
            reader.str_end = 0


def dump_motion_v4():
    read('str', 'motion_name')
    length = read('I', 'length')

    while not is_end():
        flags = read('B', 'flags')
        t_present = flags & FL_T_KEY_PRESENT
        r_absent = flags & FL_R_KEY_ABSENT
        hq = flags & KPF_T_HQ

        if r_absent:
            read('4h', 'quaternion')
        else:
            read('I', 'motion_crc32')
            for key_index in range(length):
                read('4h', 'quaternion')

        if hq:
            translate_format = '3h'
        else:
            translate_format = '3b'

        if t_present:
            read('I', 'motion_crc32')
            for key_index in range(length):
                read(translate_format, 'translate')
            read('3f', 't_size')
            read('3f', 't_init')

        else:
            read('3f', 'translate')


def dump_motion_v3_2():
    read('str', 'motion_name')
    length = read('I', 'length')

    while not is_end():
        t_present = read('B', 't_present')

        read('I', 'motion_crc32')
        for key_index in range(length):
            read('4h', 'quaternion')

        if t_present:
            read('I', 'motion_crc32')
            for key_index in range(length):
                read('3B', 'translate')
            read('3f', 't_size')
            read('3f', 't_init')

        else:
            read('3f', 'translate')


def dump_motion_v3_1():
    motion_name = read('str', 'motion_name')
    length = read('I', 'length')

    global reader

    frame_len_1 = 4 * 2 + 3 * 4
    frame_len_2 = 4 * 4 + 3 * 4
    head_len = len(motion_name) + 1 + 4
    keys_length = len(reader.data) - head_len

    x = keys_length // length
    if x % frame_len_1 == 0:
        quat_fmt = 'h'
    elif x % frame_len_2 == 0:
        quat_fmt = 'f'

    while not is_end():
        for key_index in range(length):
            read('4' + quat_fmt, 'quaternion')
            read('3f', 'translation')


def dump_motions(data, motion_fun):
    global reader

    chunks = ChunkedReader(data).read()
    count_chunk = chunks[0][1]

    reader = PackedReader(count_chunk)
    read('I', 'motions_count')
    reader.readed()

    for motion_id, motion_data in chunks[1 : ]:
        reader = PackedReader(motion_data)
        motion_fun()
        reader.readed()


def dump_p_map(data):
    chunks = ChunkedReader(data).read()
    global reader

    for chunk_id, chunk_data in chunks:
        reader = PackedReader(chunk_data)

        if chunk_id == 1:
            read('I', 'v_current')
            read('I', 'i_current')

        elif chunk_id == 2:
            count = len(chunk_data) // 4
            for index in range(count):
                read('H', 'vsplit_vert')
                read('B', 'num_new_triangles')
                read('B', 'num_fix_faces')

        elif chunk_id == 3:
            count = read('I', 'count')
            for index in range(count):
                read('H', 'face_affected')

        else:
            print('unknown chunk', chunk_id, len(chunk_data))
            raise 'error'

        reader.readed()


def dump_children(data, child_fun):
    chunks = ChunkedReader(data).read()
    for child_id, child_data in chunks:
        child_fun(child_data)


def dump_motion_refs_2():
    count = read('I', 'reference_count')
    for index in range(count):
        read('str', 'motion_reference')


def dump_lods_v4(data):
    global reader
    reader = PackedReader(data)
    read('str', 'lod_reference')

    if not is_end():
        lods_chunks = ChunkedReader(reader.data).read()
        for lod_id, lod_data in lods_chunks:
            dump_ogf_v4(lod_data)
    else:
        reader.readed()


def dump_motion_refs_0():
    read('str', 'motion_references')


def dump_user_data():
    read('str', 'userdata')


def dump_ik_data_2():
    while not is_end():
        format_version = read('I', 'format_version')

        if format_version != BONE_VERSION_1:
            raise 'Unsupported BONE format version!'

        dump_ik_data(format_version)


def dump_ik_data_1():
    while not is_end():
        dump_ik_data(BONE_VERSION_0)


def dump_ik_data_0():
    while not is_end():
        game_material=read('str', 'game_material')

        read('I', 'shape_type')

        read('9f', 'box_rotation')
        read('3f', 'box_position')
        read('3f', 'box_halfsize')

        read('3f', 'sphere_position')
        read('f', 'sphere_radius')

        read('3f', 'cylinder_position')
        read('3f', 'cylinder_direction')
        read('f', 'cylinder_height')
        read('f', 'cylinder_radius')

        read('I', 'joint_type')

        read('2f', 'limits_x')
        read('f', 'spring_x')
        read('f', 'damping_x')

        read('2f', 'limits_y')
        read('f', 'spring_y')
        read('f', 'damping_y')
    
        read('2f', 'limits_z')
        read('f', 'spring_z')
        read('f', 'damping_z')

        read('f', 'joint_spring')
        read('f', 'joint_damping')

        read('3f', 'bind_rotation')
        read('3f', 'bind_translation')

        read('f', 'mass')
        read('3f', 'mass_center')


def dump_ik_data(format_version):
    read('str', 'game_material')

    read('H', 'shape_type')
    read('H', 'shape_flags')

    read('9f', 'box_rotation')
    read('3f', 'box_position')
    read('3f', 'box_halfsize')

    read('3f', 'sphere_position')
    read('f', 'sphere_radius')

    read('3f', 'cylinder_position')
    read('3f', 'cylinder_direction')
    read('f', 'cylinder_height')
    read('f', 'cylinder_radius')

    read('I', 'joint_type')

    read('2f', 'limits_x')
    read('f', 'spring_x')
    read('f', 'damping_x')

    read('2f', 'limits_y')
    read('f', 'spring_y')
    read('f', 'damping_y')
    
    read('2f', 'limits_z')
    read('f', 'spring_z')
    read('f', 'damping_z')

    read('f', 'joint_spring')
    read('f', 'joint_damping')
    read('I', 'ik_flags')
    read('f', 'breakable_force')
    read('f', 'breakable_torque')

    if format_version > BONE_VERSION_0:
        read('f', 'friction')

    read('3f', 'bind_rotation')
    read('3f', 'bind_translation')

    read('f', 'mass')
    read('3f', 'mass_center')


def dump_bone_names():
    bones_count = read('I', 'bones_count')
    for bone_index in range(bones_count):
        read('str', 'bone_name')
        read('str', 'bone_parent')
        read('9f', 'rotation',)
        read('3f', 'translation')
        read('3f', 'half_size')


def dump_desc():
    read('str', 'source_file')
    read('str', 'build_name')
    read('I', 'build_time')
    read('str', 'create_name')
    read('I', 'create_time')
    read('str', 'modif_name')
    read('I', 'modif_time')


def dump_vertices():
    vert_fmt = read('I', 'vertex_format')
    vert_count = read('I', 'verices_count')
    global reader
    if vert_fmt in (VertFmt_v4.FVF_1L, VertFmt_v4.FVF_1L_CS):
        if vert_count * 36 == len(reader.data) - 8:
            for vert_index in range(vert_count):
                read('3f', 'coord')
                read('3f', 'normal')
                read('2f', 'uv')
                read('I', 'bone_index')
        else:
            for vert_index in range(vert_count):
                read('3f', 'coord')
                read('3f', 'normal')
                read('3f', 'tangent')
                read('3f', 'bitangent')
                read('2f', 'uv')
                read('I', 'bone_index')
    elif vert_fmt in (VertFmt_v4.FVF_2L, VertFmt_v4.FVF_2L_CS):
        for vert_index in range(vert_count):
            read('2H', 'bone_indices')
            read('3f', 'coord')
            read('3f', 'normal')
            read('3f', 'tangent')
            read('3f', 'bitangent')
            read('f', 'weight')
            read('2f', 'uv')
    elif vert_fmt == VertFmt_v4.FVF_3L_CS:
        for vert_index in range(vert_count):
            read('3H', 'bone_indices')
            read('3f', 'coord')
            read('3f', 'normal')
            read('3f', 'tangent')
            read('3f', 'bitangent')
            read('2f', 'weight')
            read('2f', 'uv')
    elif vert_fmt == VertFmt_v4.FVF_4L_CS:
        for vert_index in range(vert_count):
            read('4H', 'bone_indices')
            read('3f', 'coord')
            read('3f', 'normal')
            read('3f', 'tangent')
            read('3f', 'bitangent')
            read('3f', 'weight')
            read('2f', 'uv')
    elif vert_fmt == VertFmt_v4.FVF_OGF:
        for vert_index in range(vert_count):
            read('3f', 'coord')
            read('3f', 'normal')
            read('2f', 'uv',)


def dump_indices():
    indices_count = read('I', 'indices_count')
    read(str(indices_count) + 'H', 'index')


def dump_swi_data_v4():
    reserved = 0
    swis_count = 0
    while not reserved and not is_end():
        reserved = read('I', 'reserved_or_swis_count')
        if reserved:
            swis_count = reserved

    for index in range(swis_count):
        read('I', 'offset')
        read('H', 'triangles_count')
        read('H', 'vertices_count')


def dump_texture():
    read('str', 'texture')
    read('str', 'shader')


def dump_bsphere():
    read('3f', 'bsphere_center')
    read('f', 'bsphere_radius')


def dump_bbox():
    read('3f', 'bbox_min')
    read('3f', 'bbox_max')


def dump_header():
    read('B', 'model_type')
    read('H', 'shader_id')


def dump_chields():
    count = read('I', 'count')
    for index in range(count):
        chield = read('str', 'chield')


def dump_header_v3():
    version = read('B', 'version')

    if version != OGF_VERSION_3:
        raise 'Unsupported OGF format version!'

    dump_header()


def dump_header_v4():
    version = read('B', 'version')

    if version != OGF_VERSION_4:
        raise 'Unsupported OGF format version!'

    dump_header()
    dump_bbox()
    dump_bsphere()


###############################################################################


def test(chunk_id):
    # print(chunk_id)
    return


def dump_ogf_v4(data):
    chunks = ChunkedReader(data).read()

    global reader

    subchunks = (
        Chunks_v4.CHILDREN,
        Chunks_v4.S_MOTIONS,
        Chunks_v4.S_LODS
    )

    for chunk_id, chunk_data in chunks:

        reader = PackedReader(chunk_data)

        if chunk_id == Chunks_v4.HEADER:
            dump_header_v4()

        elif chunk_id == Chunks_v4.TEXTURE:
            dump_texture()

        elif chunk_id == Chunks_v4.VERTICES:
            dump_vertices()

        elif chunk_id == Chunks_v4.INDICES:
            dump_indices()

        elif chunk_id == Chunks_v4.SWIDATA:
            dump_swi_data_v4()

        elif chunk_id == Chunks_v4.VCONTAINER:
            test(chunk_id)

        elif chunk_id == Chunks_v4.ICONTAINER:
            test(chunk_id)

        elif chunk_id == Chunks_v4.CHILDREN:
            dump_children(chunk_data, dump_ogf_v4)

        elif chunk_id == Chunks_v4.CHILDREN_L:
            test(chunk_id)

        elif chunk_id == Chunks_v4.LODDEF2:
            test(chunk_id)

        elif chunk_id == Chunks_v4.TREEDEF2:
            test(chunk_id)

        elif chunk_id == Chunks_v4.S_BONE_NAMES:
            dump_bone_names()

        elif chunk_id == Chunks_v4.S_MOTIONS:
            dump_motions(chunk_data, dump_motion_v4)

        elif chunk_id == Chunks_v4.S_SMPARAMS:
            dump_smparams_2()

        elif chunk_id == Chunks_v4.S_IKDATA:
            dump_ik_data_2()

        elif chunk_id == Chunks_v4.S_USERDATA:
            dump_user_data()

        elif chunk_id == Chunks_v4.S_DESC:
            dump_desc()

        elif chunk_id == Chunks_v4.S_MOTION_REFS_0:
            dump_motion_refs_0()

        elif chunk_id == Chunks_v4.SWICONTAINER:
            test(chunk_id)

        elif chunk_id == Chunks_v4.GCONTAINER:
            test(chunk_id)

        elif chunk_id == Chunks_v4.FASTPATH:
            test(chunk_id)

        elif chunk_id == Chunks_v4.S_LODS:
            dump_lods_v4(chunk_data)

        elif chunk_id == Chunks_v4.S_MOTION_REFS_2:
            dump_motion_refs_2()

        else:
            print('unknown chunk', hex(chunk_id), len(chunk_data))
            raise 'error'

        if not chunk_id in subchunks:
            reader.readed()


def dump_ogf_v3(data):
    chunks = ChunkedReader(data).read()
    global reader

    subchunks = (
        Chunks_v3.CHILDREN,
        Chunks_v3.P_MAP,
        Chunks_v3.MOTIONS,
        Chunks_v3.MOTIONS2
    )

    for chunk_id, chunk_data in chunks:

        reader = PackedReader(chunk_data)

        if chunk_id == Chunks_v3.HEADER:
            dump_header_v3()

        elif chunk_id == Chunks_v3.TEXTURE:
            dump_texture()

        elif chunk_id == Chunks_v3.VERTICES:
            dump_vertices()

        elif chunk_id == Chunks_v3.INDICES:
            dump_indices()

        elif chunk_id == Chunks_v3.BBOX:
            dump_bbox()

        elif chunk_id == Chunks_v3.BSPHERE:
            dump_bsphere()

        elif chunk_id == Chunks_v3.P_MAP:
            dump_p_map(chunk_data)

        elif chunk_id == Chunks_v3.CHIELDS:
            dump_chields()

        elif chunk_id == Chunks_v3.MOTION_REFS:
            dump_motion_refs_0()

        elif chunk_id == Chunks_v3.DESC:
            dump_desc()

        elif chunk_id == Chunks_v3.USERDATA:
            dump_user_data()

        elif chunk_id == Chunks_v3.BONE_NAMES:
            dump_bone_names()

        elif chunk_id == Chunks_v3.IKDATA_obs:
            dump_ik_data_0()

        elif chunk_id == Chunks_v3.IKDATA2:
            dump_ik_data_2()

        elif chunk_id == Chunks_v3.IKDATA:
            dump_ik_data_1()

        elif chunk_id == Chunks_v3.SMPARAMS:
            dump_smparams_1()

        elif chunk_id == Chunks_v3.SMPARAMS2:
            dump_smparams_2()

        elif chunk_id == Chunks_v3.MOTIONS:
            dump_motions(chunk_data, dump_motion_v3_1)

        elif chunk_id == Chunks_v3.MOTIONS2:
            dump_motions(chunk_data, dump_motion_v3_2)

        elif chunk_id == Chunks_v3.CHILDREN:
            dump_children(chunk_data, dump_ogf_v3)

        else:
            print('unknown chunk', chunk_id, len(chunk_data))
            raise 'error'

        if not chunk_id in subchunks:
            reader.readed()


def dump_ogf(data):
    chunks = ChunkedReader(data).read()
    global reader

    for chunk_id, chunk_data in chunks:
        if chunk_id == 0x1:    # HEADER
            reader = PackedReader(chunk_data)
            version = read('B', 'version')

            if version == OGF_VERSION_3:
                dump_ogf_v3(data)

            elif version == OGF_VERSION_4:
                dump_ogf_v4(data)

            else:
                print('unsupported ogf version:', version)
                raise 'error'

            break


###############################################################################


def is_end():
    global reader
    return reader.is_end()


def read(fmt, name):
    if fmt == 'str':
        value = reader.gets()
    else:
        value = reader.getf('<' + fmt)
        if len(value) == 1:
            value = value[0]
    # print('{} = {}'.format(name, value))
    return value


directory = 'D:\\stalker\\all_builds_gamedata\\'

ogf_list = []
for root, dirs, files in os.walk(directory):
    for file_name in files:
        ext = os.path.splitext(file_name)[-1]
        if ext in ('.ogf', '.omf'):
            path = os.path.join(root, file_name)
            path = os.path.abspath(path)
            ogf_list.append(path)

for path in reversed(ogf_list):
    with open(path, 'rb') as file:
        data = file.read()
    print('dump file: "{}"'.format(path))
    dump_ogf(data)
