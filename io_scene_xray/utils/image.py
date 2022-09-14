# standart modules
import os

# blender modules
import bpy

# addon modules
from .. import log
from .. import text


def _make_relative_texture_path(texture_file_path, textures_folder):
    texture_file_path = texture_file_path[len(textures_folder) : ]
    texture_file_path = texture_file_path.replace(os.path.sep, '\\')
    if texture_file_path.startswith('\\'):
        texture_file_path = texture_file_path[1 : ]
    return texture_file_path


def _gen_tex_name_by_textures_folder(tex_path, textures_folder, image):
    if tex_path.startswith(textures_folder):
        # when the texture path is valid
        tex_path = _make_relative_texture_path(tex_path, textures_folder)

    else:
        # automatically fix relative path
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
        log.warn(
            text.warn.img_bad_image_path,
            image=image.name,
            image_path=image.filepath,
            textures_folder=textures_folder,
            saved_as=tex_path
        )

    return tex_path


def _gen_tex_name_by_level_folder(
        tex_path,
        textures_folder,
        level_folder,
        image,
        file_path,
        errors
    ):
    if tex_path.startswith(textures_folder):
        # gamedata\textures folder
        tex_path = _make_relative_texture_path(tex_path, textures_folder)

    elif tex_path.startswith(level_folder):
        # gamedata\levels\level_name folder
        tex_path = _make_relative_texture_path(tex_path, level_folder)

    else:
        # gamedata\levels\level_name\texture_name
        tex_path = os.path.split(tex_path)[-1]
        if not file_path in errors:
            log.warn(
                text.warn.invalid_image_path,
                image=image.name,
                path=file_path,
                textures_folder=textures_folder,
                saved_as=tex_path
            )
            errors.add(file_path)

    return tex_path


def gen_texture_name(image, textures_folder, level_folder=None, errors=set()):
    file_path = image.filepath
    tex_path = bpy.path.abspath(file_path)
    tex_path = os.path.normpath(tex_path)
    tex_path = os.path.splitext(tex_path)[0]
    textures_folder = os.path.abspath(textures_folder)

    if level_folder:
        # use level folder
        tex_rel_path = _gen_tex_name_by_level_folder(
            tex_path,
            textures_folder,
            level_folder,
            image,
            file_path,
            errors
        )
    else:
        # find texture in gamedata\textures folder
        tex_rel_path = _gen_tex_name_by_textures_folder(
            tex_path,
            textures_folder,
            image
        )

    return tex_rel_path
