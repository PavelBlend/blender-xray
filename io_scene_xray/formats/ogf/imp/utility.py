# standart modules
import os
 
# blender modules
import mathutils

# addon modules
from .. import fmt
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
    if not chunks:
        return

    chunks_ids = list(chunks.keys())
    chunks_ids.sort()

    for chunk_id in chunks_ids:
        data = chunks[chunk_id]
        size = len(data)
        print('Unknown OGF {} Chunk: {} ({} bytes)'.format(
            context,
            chunk_id,
            size
        ))


def get_ogf_chunks(data):
    chunked_reader = rw.read.ChunkedReader(data)

    chunks = {}

    for chunk_id, chunkd_data in chunked_reader:
        chunks[chunk_id] = chunkd_data

    return chunks


def set_export_path(context, visual, bpy_object):
    meshes_folder = context.meshes_folder.lower()
    if not meshes_folder:
        return

    file_path = visual.file_path.lower()
    if not file_path.startswith(meshes_folder):
        return

    file_dir = os.path.dirname(file_path)
    offset = len(meshes_folder)
    exp_path = file_dir[offset : ]

    bpy_object.xray.export_path = exp_path


def set_visual_type(visual, root_visual):
    if visual.format_version == fmt.FORMAT_VERSION_4:
        model_types = fmt.ModelType_v4
    elif visual.format_version == fmt.FORMAT_VERSION_3:
        model_types = fmt.ModelType_v3

    if visual.model_type == model_types.SKELETON_GEOMDEF_PM:
        root_visual.arm_obj.xray.flags_simple = 'pd'

    elif visual.model_type == model_types.SKELETON_GEOMDEF_ST:
        root_visual.arm_obj.xray.flags_simple = 'dy'

    elif visual.model_type == model_types.PROGRESSIVE:
        root_visual.root_obj.xray.flags_simple = 'pd'

    elif visual.model_type == model_types.NORMAL:
        root_visual.root_obj.xray.flags_simple = 'dy'

    else:
        print('WARNING: Model type = {}'.format(visual.model_type))
