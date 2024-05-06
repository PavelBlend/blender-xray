# standart modules
import os

# addon modules
from . import fmt
from ... import rw


def _read_type(chunks):
    type_chunk = chunks.pop(fmt.ThmChunks.TYPE)
    packed_reader = rw.read.PackedReader(type_chunk)
    thm_type = packed_reader.getf('<I')[0]
    return thm_type


def _read_version(chunks):
    version_chunk = chunks.pop(fmt.ThmChunks.VERSION)
    packed_reader = rw.read.PackedReader(version_chunk)
    version = packed_reader.getf('<H')[0]
    return version


def _read_bump(chunks):
    bump_chunk = chunks.pop(fmt.ThmTextureChunks.BUMP, None)

    if not bump_chunk:
        return

    packed_reader = rw.read.PackedReader(bump_chunk)

    packed_reader.skip(8)    # 4 bytes: virtual height, 4 bytes: bump mode
    bump_name = packed_reader.gets()

    return bump_name


def _get_bump_name(file_data):
    chunks = rw.utils.get_chunks(file_data)

    # check type
    thm_type = _read_type(chunks)
    if thm_type != fmt.ThmType.TEXTURE:
        return

    # check version
    version = _read_version(chunks)
    if version != fmt.ThmVersion.TEXTURE:
        return

    # read bump
    bump_name = _read_bump(chunks)
    return bump_name


def get_bump_paths(file_data):
    bump_name = _get_bump_name(file_data)
    ext = os.extsep + 'dds'

    if bump_name:
        bump_1_rel = bump_name + ext
        bump_2_rel = bump_name + '#' + ext
        return bump_1_rel, bump_2_rel
    else:
        return None, None
