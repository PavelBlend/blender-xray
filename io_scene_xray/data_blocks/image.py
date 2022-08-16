# standart modules
import os

# blender modules
import bpy

# addon modules
from .. import log
from .. import text


def make_relative_texture_path(a_tx_fpath, a_tx_folder):
    a_tx_fpath = a_tx_fpath[len(a_tx_folder):].replace(os.path.sep, '\\')
    if a_tx_fpath.startswith('\\'):
        a_tx_fpath = a_tx_fpath[1:]
    return a_tx_fpath


def gen_texture_name(image, tx_folder, level_folder=None, errors=set()):
    file_path = image.filepath
    a_tx_fpath = os.path.normpath(bpy.path.abspath(file_path))
    a_tx_folder = os.path.abspath(tx_folder)
    a_tx_fpath = os.path.splitext(a_tx_fpath)[0]
    if not level_folder:    # find texture in gamedata\textures folder
        if not a_tx_fpath.startswith(a_tx_folder):
            drive, path_part_1 = os.path.splitdrive(a_tx_fpath)
            file_full_name = os.path.basename(path_part_1)
            file_name, ext = os.path.splitext(file_full_name)
            if path_part_1.count(os.sep) > 1:
                dir_path = os.path.dirname(path_part_1)
                dir_name = os.path.basename(dir_path)
                if file_name.startswith(dir_name + '_'):
                    relative_path = os.path.join(dir_name, file_name)
                    a_tx_fpath = relative_path.replace(os.path.sep, '\\')
                else:
                    a_tx_fpath = file_name
            else:
                a_tx_fpath = file_name
            log.warn(
                text.warn.img_bad_image_path,
                image=image.name,
                image_path=image.filepath,
                textures_folder=a_tx_folder,
                saved_as=a_tx_fpath
            )
        else:
            a_tx_fpath = make_relative_texture_path(a_tx_fpath, a_tx_folder)
    else:
        if a_tx_fpath.startswith(a_tx_folder):    # gamedata\textures folder
            a_tx_fpath = make_relative_texture_path(a_tx_fpath, a_tx_folder)
        elif a_tx_fpath.startswith(level_folder):    # gamedata\levels\level_name folder
            a_tx_fpath = make_relative_texture_path(a_tx_fpath, level_folder)
        else:    # gamedata\levels\level_name\texture_name
            if not file_path in errors:
                log.warn(
                    text.warn.invalid_image_path,
                    image=image.name,
                    path=file_path
                )
                errors.add(file_path)
            a_tx_fpath = os.path.split(a_tx_fpath)[-1]
    return a_tx_fpath
