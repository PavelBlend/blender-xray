# addon modules
from .. import fmt
from .... import text
from .... import rw
from .... import log
from .... import utils


def _search_material(bpy_obj):
    used_materials = utils.version.get_used_mats(bpy_obj.data)

    # check without materials
    if not len(bpy_obj.data.materials):
        raise log.AppError(
            text.error.obj_no_mat,
            log.props(object=bpy_obj.name)
        )

    # check empty material slot
    for mat_index in used_materials:
        material = bpy_obj.data.materials[mat_index]
        if not material:
            raise log.AppError(
                text.error.obj_empty_mat,
                log.props(object=bpy_obj.name)
            )

    # collect object materials
    materials = set()

    for mat_index, material in enumerate(bpy_obj.data.materials):

        if not material:
            continue

        if not mat_index in used_materials:
            continue

        materials.add(material)

    materials = list(materials)

    # check materials count
    if not len(materials):
        raise log.AppError(
            text.error.obj_no_mat,
            log.props(object=bpy_obj.name)
        )

    elif len(materials) > 1:
        raise log.AppError(
            text.error.many_mat,
            log.props(object=bpy_obj.name)
        )

    material = materials[0]
    two_sided = material.xray.flags_twosided

    return material, two_sided


def _write_chunk(texture_path, material, chunked_writer):
    texture_writer = rw.write.PackedWriter()

    texture_writer.puts(texture_path)
    texture_writer.puts(material.xray.eshader)

    chunked_writer.put(fmt.Chunks_v4.TEXTURE, texture_writer)


def write_tex(bpy_obj, context, chunked_writer):
    # search material
    material, two_sided = _search_material(bpy_obj)

    # generate texture path
    texture_path = utils.material.get_image_relative_path(
        material,
        context,
        no_err=False
    )

    # write texture chunk
    _write_chunk(texture_path, material, chunked_writer)

    return two_sided
