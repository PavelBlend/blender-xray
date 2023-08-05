# standart modules
import os

# blender modules
import bpy

# addon modules
from . import tex
from .. import log
from .. import text


def _make_relative_texture_path(texture_file_path, tex_folder):
    texture_file_path = texture_file_path[len(tex_folder) : ]
    texture_file_path = texture_file_path.replace(os.path.sep, '\\')
    if texture_file_path.startswith('\\'):
        texture_file_path = texture_file_path[1 : ]
    texture_file_path = os.path.splitext(texture_file_path)[0]
    return texture_file_path


def _gen_relative_path(tex_path):
    drive, path_part_1 = os.path.splitdrive(tex_path)
    file_full_name = os.path.basename(path_part_1)
    file_name, ext = os.path.splitext(file_full_name)
    if path_part_1.count(os.sep) > 1:
        dir_path = os.path.dirname(path_part_1)
        dir_name = os.path.basename(dir_path)
        if file_name.startswith(dir_name + '_'):
            relative_path = os.path.join(dir_name, file_name)
            tex_path = relative_path.replace(os.path.sep, '\\')
        else:
            tex_path = file_name
    else:
        tex_path = file_name
    return tex_path


def _gen_tex_name_by_textures_folder(tex_path, context, image):
    # collect texture folders
    tex_dirs = []
    if context.level_name:
        for folder in (context.lvl_mod_folder, context.lvl_folder):
            if folder:
                level_folder = os.path.join(folder, context.level_name)
                tex_dirs.append(level_folder)
    tex_dirs.extend([context.tex_mod_folder, context.tex_folder])

    rel_path = None

    # collect texture absolute paths
    abs_paths = []
    for tex_dir in tex_dirs:
        if not tex_dir:
            continue

        if tex_path.startswith(tex_dir):
            # when the texture path is valid
            rel_path = _make_relative_texture_path(tex_path, tex_dir)
            break

    if not rel_path:
        # automatically fix relative path
        rel_path = _gen_relative_path(tex_path)
        image_abs_path = bpy.path.abspath(image.filepath)
        log.warn(
            text.warn.img_bad_image_path,
            image=image.name,
            image_path=image_abs_path,
            textures_folder=context.tex_folder,
            saved_as=rel_path
        )

    return rel_path


def gen_texture_name(image, context, level_folder=None, errors=None):
    file_path = image.filepath
    tex_path = bpy.path.abspath(file_path)
    tex_path = os.path.normpath(tex_path)

    tex_rel_path = _gen_tex_name_by_textures_folder(tex_path, context, image)

    return tex_rel_path
