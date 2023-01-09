# blender modules
import bpy

# addon modules
from . import lod
from . import load
from . import tree
from . import shader
from .. import fmt
from ... import level
from .... import utils
from .... import log
from .... import text


def import_model_v4(chunks, visual, lvl):

    if visual.model_type == fmt.ModelType_v4.NORMAL:
        bpy_obj = load.import_normal_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v4.HIERRARHY:
        bpy_obj = load.import_hierrarhy_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v4.PROGRESSIVE:
        bpy_obj = load.import_progressive_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v4.TREE_ST:
        bpy_obj = tree.import_tree_st_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v4.TREE_PM:
        bpy_obj = tree.import_tree_pm_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v4.LOD:
        bpy_obj = lod.import_lod_visual(chunks, visual, lvl)

    else:
        raise BaseException('unsupported model type: {:x}'.format(
            visual.model_type
        ))

    data = bpy_obj.xray
    data.is_ogf = True

    collection_name = level.create.LEVEL_VISUALS_COLLECTION_NAMES_TABLE[visual.name]
    collection = lvl.collections[collection_name]
    collection.objects.link(bpy_obj)
    if utils.version.IS_28:
        scene_collection = bpy.context.scene.collection
        scene_collection.objects.unlink(bpy_obj)
    lvl.visuals.append(bpy_obj)


def import_model_v3(chunks, visual, lvl):
    chunks_ids = fmt.Chunks_v3
    if visual.model_type == fmt.ModelType_v3.NORMAL:
        texture_l_data = chunks.get(chunks_ids.TEXTURE_L)
        if texture_l_data:
            chunks.pop(chunks_ids.TEXTURE_L)
            shader.import_texture_and_shader_v3(visual, lvl, texture_l_data)
        bpy_obj = load.import_normal_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v3.HIERRARHY:
        bpy_obj = load.import_hierrarhy_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v3.TREE:
        texture_l_data = chunks.get(chunks_ids.TEXTURE_L)
        if texture_l_data:
            chunks.pop(chunks_ids.TEXTURE_L)
            shader.import_texture_and_shader_v3(visual, lvl, texture_l_data)
        bpy_obj = tree.import_tree_st_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v3.LOD:
        texture_l_data = chunks.get(chunks_ids.TEXTURE_L)
        if texture_l_data:
            chunks.pop(chunks_ids.TEXTURE_L)
            shader.import_texture_and_shader_v3(visual, lvl, texture_l_data)
        bpy_obj = lod.import_lod_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v3.CACHED:
        texture_l_data = chunks.get(chunks_ids.TEXTURE_L)
        if texture_l_data:
            chunks.pop(chunks_ids.TEXTURE_L)
            shader.import_texture_and_shader_v3(visual, lvl, texture_l_data)
        bpy_obj = load.import_normal_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v3.PROGRESSIVE2:
        ####################################################
        # DELETE
        ####################################################
        bpy_obj = bpy.data.objects.new('PROGRESSIVE2', None)
        bpy.context.scene.collection.objects.link(bpy_obj)
        visual.name = 'progressive'

    else:
        raise log.AppError(
            text.error.ogf_bad_model_type,
            log.props(model_type=visual.model_type)
        )

    data = bpy_obj.xray
    data.is_ogf = True

    collection_name = level.create.LEVEL_VISUALS_COLLECTION_NAMES_TABLE[visual.name]
    collection = lvl.collections[collection_name]
    collection.objects.link(bpy_obj)
    if utils.version.IS_28:
        scene_collection = bpy.context.scene.collection
        scene_collection.objects.unlink(bpy_obj)
    lvl.visuals.append(bpy_obj)


def import_model_v2(chunks, visual, lvl):
    chunks_ids = fmt.Chunks_v2
    if visual.model_type == fmt.ModelType_v2.NORMAL:
        texture_l_data = chunks.pop(chunks_ids.TEXTURE_L)
        shader.import_texture_and_shader_v3(visual, lvl, texture_l_data)
        bpy_obj = load.import_normal_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v2.HIERRARHY:
        bpy_obj = load.import_hierrarhy_visual(chunks, visual, lvl)
    else:
        raise log.AppError(
            text.error.ogf_bad_model_type,
            log.props(model_type=visual.model_type)
        )

    data = bpy_obj.xray
    data.is_ogf = True

    scene_collection = bpy.context.scene.collection
    collection_name = level.create.LEVEL_VISUALS_COLLECTION_NAMES_TABLE[visual.name]
    collection = lvl.collections[collection_name]
    collection.objects.link(bpy_obj)
    scene_collection.objects.unlink(bpy_obj)
    lvl.visuals.append(bpy_obj)
