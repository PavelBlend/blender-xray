# standart modules
import os

# blender modules
import bpy

# addon modules
from .... import utils


def is_same_image_paths(bpy_img, abs_texture_path):
    abs_img_path = bpy.path.abspath(bpy_img.filepath)
    return abs_img_path == abs_texture_path


def _add_texture_ext(texture):
    return texture + os.extsep + 'dds'


def _get_abs_tex_path(folder, texture):
    return os.path.join(folder, _add_texture_ext(texture))


def _load_lmap_img(context, path):
    lmap_img = context.image(path)
    lmap_img.colorspace_settings.name = 'Non-Color'
    lmap_img.use_fake_user = True
    return lmap_img


def get_image_lmap(context, light_maps):
    if not light_maps:
        return None

    light_maps_count = len(light_maps)

    if light_maps_count == 1:
        lmap_img = _load_lmap_img(context, light_maps[0])
        lmap_imgs = (lmap_img, )

    elif light_maps_count == 2:
        lmap_img_1 = _load_lmap_img(context, light_maps[0])
        lmap_img_2 = _load_lmap_img(context, light_maps[1])
        lmap_imgs = (lmap_img_1, lmap_img_2)

    return lmap_imgs


def is_same_light_maps(context, bpy_mat, light_maps):
    has_images = []
    level_dir = os.path.dirname(context.filepath)

    for index, light_map in enumerate(light_maps):
        # absolute texture path in level folder
        abs_lvl_path = _get_abs_tex_path(level_dir, light_map)
        image_name = getattr(bpy_mat.xray, 'lmap_{}'.format(index))
        bpy_image = bpy.data.images.get(image_name)

        if not bpy_image:
            continue

        if not is_same_image_paths(bpy_image, abs_lvl_path):
            continue

        has_images.append(True)

    if len(has_images) == len(light_maps):
        return True


def is_same_image(context, bpy_mat, texture):
    level_dir = os.path.dirname(context.filepath)
    # absolute texture path in textures folder
    abs_tex_path = _get_abs_tex_path(context.tex_folder, texture)
    # absolute texture path in level folder
    abs_lvl_path = _get_abs_tex_path(level_dir, texture)

    if utils.version.IS_28:
        for node in bpy_mat.node_tree.nodes:
            if node.type in utils.version.IMAGE_NODES:
                bpy_image = node.image

                if not bpy_image:
                    continue

                if not is_same_image_paths(bpy_image, abs_lvl_path):
                    if not is_same_image_paths(bpy_image, abs_tex_path):
                        continue

                return bpy_image

    else:
        for texture_slot in bpy_mat.texture_slots:

            if not texture_slot:
                continue

            if not hasattr(texture_slot.texture, 'image'):
                continue

            bpy_image = texture_slot.texture.image

            if not bpy_image:
                continue

            if not is_same_image_paths(bpy_image, abs_lvl_path):
                if not is_same_image_paths(bpy_image, abs_tex_path):
                    continue

            return bpy_image
