# addon modules
from .... import utils
from .... import rw


def import_texture_and_shader_v3(visual, lvl, data):
    packed_reader = rw.read.PackedReader(data)
    visual.texture_id = packed_reader.uint32()
    visual.shader_id = packed_reader.uint32()


def read_texture_l(chunks, ogf_chunks, visual, lvl):
    texture_l_data = chunks.pop(ogf_chunks.TEXTURE_L, None)
    if texture_l_data:
        import_texture_and_shader_v3(visual, lvl, texture_l_data)


def read_texture(context, chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.TEXTURE)
    packed_reader = rw.read.PackedReader(chunk_data)

    texture = packed_reader.gets()
    shader = packed_reader.gets()

    bpy_material, bpy_image = utils.material.get_material(
        context,
        texture,    # material name
        texture,
        shader,
        'default',    # compile shader
        'default_object',    # game material
        0,    # two sided flag
        'Texture'    # uv map name
    )

    visual.bpy_material = bpy_material
    visual.bpy_image = bpy_image
