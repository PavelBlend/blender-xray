# standart modules
import os

# blender modules
import bpy

# addon modules
from . import stats


def create_empty_img(tex_path):
    img_name = os.path.basename(tex_path)
    bpy_img = bpy.data.images.new(img_name, 0, 0)
    bpy_img.source = 'FILE'
    bpy_img.filepath = tex_path
    stats.created_img()

    return bpy_img


def normalize_tex_relpath(tex_relpath):
    return tex_relpath.lower().replace('\\', os.path.sep)


def add_tex_ext(tex_path):
    return tex_path + '.dds'


def make_abs_tex_path(tex_folder, tex_relpath):
    return os.path.abspath(os.path.join(tex_folder, add_tex_ext(tex_relpath)))


def search_image_by_tex_path(tex_abspath):
    for bpy_image in bpy.data.images:
        if bpy.path.abspath(bpy_image.filepath) == tex_abspath:
            return bpy_image


def load_image_by_tex_path(tex_abspath):
    if os.path.exists(tex_abspath):

        try:
            bpy_img = bpy.data.images.load(tex_abspath)
            stats.created_img()
            return bpy_img

        except RuntimeError:    # e.g. 'Error: Cannot read ...'
            pass
