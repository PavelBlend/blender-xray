# standart modules
import os

# blender modules
import bpy

# addon modules
from . import types
from .. import fmt
from .... import utils
from .... import log
from .... import text
from .... import rw


def _get_light_map_image(material, lmap_prop):
    lmap_image_name = getattr(material.xray, lmap_prop, None)

    if lmap_image_name:
        lmap_image = bpy.data.images.get(lmap_image_name, None)
        if not lmap_image:
            raise log.AppError(
                text.error.level_no_lmap,
                log.props(
                    light_map=lmap_image_name,
                    material=material.name
                )
            )
        image_path = lmap_image.filepath
        image_name = os.path.basename(image_path)
        base_name, ext = os.path.splitext(image_name)
        if ext != '.dds':
            raise log.AppError(
                text.error.level_lmap_no_dds,
                log.props(
                    image=lmap_image.name,
                    path=lmap_image.filepath,
                    extension=ext
                )
            )
        lmap_name = base_name

    else:
        lmap_image = None
        lmap_name = None

    return lmap_image, lmap_name


def write_shaders(level_writer, level):
    texture_folder = utils.version.get_preferences().textures_folder_auto

    materials = {}
    for material, shader_index in level.materials.items():
        materials[shader_index] = material

    materials_count = len(materials)
    shaders_writer = rw.write.PackedWriter()
    shaders_writer.putf('<I', materials_count + 1)    # shaders count
    shaders_writer.puts('')    # first empty shader
    context = types.ExportLevelContext(texture_folder)

    for shader_index in range(materials_count):
        material = materials[shader_index]
        texture_path = utils.material.get_image_relative_path(
            material,
            context,
            level_folder=level.source_level_path,
            no_err=False
        )

        eshader = material.xray.eshader

        lmap_1_image, lmap_1_name = _get_light_map_image(material, 'lmap_0')
        lmap_2_image, lmap_2_name = _get_light_map_image(material, 'lmap_1')

        # lightmap shader
        if lmap_1_image and lmap_2_image:
            shaders_writer.puts('{0}/{1},{2},{3}'.format(
                eshader,
                texture_path,
                lmap_1_name,
                lmap_2_name
            ))

        # terrain shader
        elif lmap_1_image and not lmap_2_image:
            lmap_1_path = utils.image.gen_texture_name(
                lmap_1_image,
                texture_folder,
                level_folder=level.source_level_path
            )
            shaders_writer.puts('{0}/{1},{2}'.format(
                eshader,
                texture_path,
                lmap_1_path
            ))

        # vertex colors shader
        else:
            shaders_writer.puts('{0}/{1}'.format(eshader, texture_path))

    level_writer.put(fmt.Chunks13.SHADERS, shaders_writer)


def get_shader_index(level, obj, no_mat_text, many_mats_text, empty_mat_text):
    mesh = obj.data

    mats_count = len(mesh.materials)
    if not mats_count:
        raise log.AppError(
            no_mat_text,
            log.props(object=obj.name)
        )

    if mats_count == 1:
        bpy_mat = mesh.materials[0]
        if not bpy_mat:
            raise log.AppError(
                empty_mat_text,
                log.props(object=obj.name)
            )

    else:
        mats = set()
        for face in mesh.polygons:
            mat = mesh.materials[face.material_index]
            if mat:
                mats.add(mat)
        mats = list(mats)

        if len(mats) == 1:
            bpy_mat = mats[0]
            if not bpy_mat:
                raise log.AppError(
                    empty_mat_text,
                    log.props(object=obj.name)
                )
        else:
            raise log.AppError(
                many_mats_text,
                log.props(
                    object=obj.name,
                    materials=[mat.name for mat in mats]
                )
            )

    shader_index = level.materials.get(bpy_mat, None)

    if shader_index is None:
        shader_index = level.active_material_index
        level.active_material_index += 1
        level.materials[bpy_mat] = shader_index

    return bpy_mat, shader_index
