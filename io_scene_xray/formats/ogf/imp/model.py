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


def link_visual_object(lvl, visual, bpy_obj):
    coll_name = level.imp.name.LEVEL_VISUALS_COLLECTION_NAMES_TABLE[visual.name]
    collection = lvl.collections[coll_name]
    collection.objects.link(bpy_obj)

    if utils.version.IS_28:
        scene_collection = bpy.context.scene.collection
        scene_collection.objects.unlink(bpy_obj)


def import_model_v4(chunks, visual, lvl):
    chunks_fmt = fmt.Chunks_v4

    if visual.model_type == fmt.ModelType_v4.NORMAL:
        bpy_obj = load.import_normal_visual(chunks, visual, lvl, chunks_fmt)

    elif visual.model_type == fmt.ModelType_v4.HIERRARHY:
        bpy_obj = load.import_hierrarhy_visual(chunks, chunks_fmt, visual, lvl)

    elif visual.model_type == fmt.ModelType_v4.PROGRESSIVE:
        bpy_obj = load.import_progressive_visual(chunks, visual, lvl, chunks_fmt)

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

    bpy_obj.xray.is_ogf = True
    lvl.visuals.append(bpy_obj)
    link_visual_object(lvl, visual, bpy_obj)


def import_model_v3(chunks, visual, lvl):
    chunks_ids = fmt.Chunks_v3
    shader.read_texture_l(chunks, chunks_ids, visual, lvl)

    if visual.model_type == fmt.ModelType_v3.NORMAL:
        bpy_obj = load.import_normal_visual(chunks, visual, lvl, chunks_ids)

    elif visual.model_type == fmt.ModelType_v3.HIERRARHY:
        bpy_obj = load.import_hierrarhy_visual(chunks, chunks_ids, visual, lvl)

    elif visual.model_type == fmt.ModelType_v3.TREE:
        bpy_obj = tree.import_tree_st_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v3.LOD:
        bpy_obj = lod.import_lod_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v3.CACHED:
        bpy_obj = load.import_normal_visual(chunks, visual, lvl, chunks_ids)

    else:
        raise log.AppError(
            text.error.ogf_bad_model_type,
            log.props(model_type=visual.model_type)
        )

    bpy_obj.xray.is_ogf = True
    lvl.visuals.append(bpy_obj)
    link_visual_object(lvl, visual, bpy_obj)


def import_model_v2(chunks, visual, lvl):
    chunks_ids = fmt.Chunks_v2

    if visual.model_type == fmt.ModelType_v2.NORMAL:
        shader.read_texture_l(chunks, chunks_ids, visual, lvl)
        bpy_obj = load.import_normal_visual(chunks, visual, lvl, chunks_ids)

    elif visual.model_type == fmt.ModelType_v2.HIERRARHY:
        bpy_obj = load.import_hierrarhy_visual(chunks, chunks_ids, visual, lvl)

    else:
        raise log.AppError(
            text.error.ogf_bad_model_type,
            log.props(model_type=visual.model_type)
        )

    bpy_obj.xray.is_ogf = True
    lvl.visuals.append(bpy_obj)
    link_visual_object(lvl, visual, bpy_obj)
