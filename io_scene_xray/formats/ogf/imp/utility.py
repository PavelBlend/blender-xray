# standart modules
import os
 
# blender modules
import mathutils

# addon modules
from .... import rw


def convert_normal(norm_in):
    norm_out_x = 2.0 * norm_in[0] / 255 - 1.0
    norm_out_y = 2.0 * norm_in[1] / 255 - 1.0
    norm_out_z = 2.0 * norm_in[2] / 255 - 1.0
    return mathutils.Vector((norm_out_x, norm_out_y, norm_out_z)).normalized()


def convert_float_normal(norm_in):
    return mathutils.Vector((norm_in[0], norm_in[1], norm_in[2])).normalized()


def get_float_rgb_hemi(rgb_hemi):
    hemi = (rgb_hemi & (0xff << 24)) >> 24
    red = (rgb_hemi & (0xff << 16)) >> 16
    green = (rgb_hemi & (0xff << 8)) >> 8
    blue = rgb_hemi & 0xff
    return red / 0xff, green / 0xff, blue / 0xff, hemi / 0xff


def check_unread_chunks(chunks, context=''):
    chunks_ids = list(chunks.keys())
    chunks_ids.sort()
    if chunks:
        print('There are OGF unread {1} chunks: {0}'.format(
            list(map(hex, chunks_ids)), context
        ))


def get_ogf_chunks(data):
    chunked_reader = rw.read.ChunkedReader(data)

    chunks = {}

    for chunk_id, chunkd_data in chunked_reader:
        chunks[chunk_id] = chunkd_data

    return chunks


def check_unreaded_chunks(chunks):
    for chunk_id, chunk_data in chunks.items():
        size = len(chunk_data)
        name = hex(chunk_id)
        print('Unknown OGF chunk: {}, size: {}'.format(name, size))


def set_export_path(context, visual, bpy_object):
    meshes = context.meshes_folder.lower()
    if not meshes:
        return

    file_path = visual.file_path.lower()
    if not file_path.startswith(meshes):
        return

    file_dir = os.path.dirname(file_path)
    offset = len(meshes)
    exp_path = file_dir[offset : ]
    arm = visual.arm_obj

    if arm:
        arm.xray.export_path = exp_path
    else:
        bpy_object.xray.export_path = exp_path
