# addon modules
from .. import fmt
from ... import level


def get_level_material(lvl, shader_id, texture_id):
    material_key = (shader_id, texture_id)
    bpy_material = lvl.materials.get(material_key, None)

    if not bpy_material:

        if not (lvl.shaders and lvl.textures):
            shader_raw = lvl.shaders_or_textures[shader_id]
            texture_raw = lvl.shaders_or_textures[texture_id]
        else:
            shader_raw = lvl.shaders[shader_id]
            texture_raw = lvl.textures[texture_id]

        shader_data = shader_raw + '/' + texture_raw
        bpy_material, bpy_image = level.shaders.import_shader(
            lvl,
            lvl.context,
            shader_data
        )
        lvl.materials[material_key] = bpy_material
        lvl.images[texture_id] = bpy_image

    return bpy_material


def assign_level_material(bpy_mesh, visual, lvl):
    if (
            visual.format_version == fmt.FORMAT_VERSION_4 or
            lvl.xrlc_version >= level.fmt.VERSION_12
        ):
        shader_id = visual.shader_id
        bpy_material = lvl.materials[shader_id]
    else:
        bpy_material = get_level_material(
            lvl,
            visual.shader_id,
            visual.texture_id
        )
    bpy_mesh.materials.append(bpy_material)
