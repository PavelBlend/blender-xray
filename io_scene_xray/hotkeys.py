# blender modules
import bpy

# addon modules
from . import prefs

# plugin modules
from .anm import ops as anm_ops
from .bones import ops as bones_ops
from .details import ops as details_ops
from .dm import ops as dm_ops
from .err import ops as err_ops
from .level import ops as level_ops
from .obj.imp import ops as imp_object_ops
from .obj.exp import ops as exp_object_ops
from .ogf import ops as ogf_ops
from .omf import ops as omf_ops
from .scene import ops as scene_ops
from .skl import ops as skl_ops


addon_hotkeys = {}

keymap_items_list = (
    # operator, key, shift, ctrl, alt
    (imp_object_ops.XRAY_OT_import_object, 'F5', False, False, False),
    (exp_object_ops.XRAY_OT_export_object, 'F5', False, False, True),
    (skl_ops.XRAY_OT_import_skls, 'F6', False, False, False),
    (skl_ops.XRAY_OT_export_skls, 'F6', False, False, True),
    (omf_ops.XRAY_OT_import_omf, 'F7', False, False, False),
    (omf_ops.XRAY_OT_export_omf, 'F7', False, False, True),
    (anm_ops.XRAY_OT_import_anm, 'F8', False, False, False),
    (anm_ops.XRAY_OT_export_anm, 'F8', False, False, True),
    (level_ops.XRAY_OT_import_level, 'F5', False, True, False),
    (level_ops.XRAY_OT_export_level, 'F5', False, True, True),
    (scene_ops.XRAY_OT_import_scene_selection, 'F6', False, True, False),
    (scene_ops.XRAY_OT_export_scene_selection, 'F6', False, True, True),
    (bones_ops.XRAY_OT_import_bones, 'F7', False, True, False),
    (bones_ops.XRAY_OT_export_bones, 'F7', False, True, True),
    (details_ops.XRAY_OT_import_details, 'F8', False, True, False),
    (details_ops.XRAY_OT_export_details, 'F8', False, True, True),
    (dm_ops.XRAY_OT_import_dm, 'F5', True, True, False),
    (dm_ops.XRAY_OT_export_dm, 'F5', True, True, True),
    (err_ops.XRAY_OT_import_err, 'F6', True, True, False),
    (ogf_ops.XRAY_OT_export_ogf, 'F7', True, True, True)
)


def register():
    preferences = prefs.utils.get_preferences()
    win_manager = bpy.context.window_manager
    keyconfig = win_manager.keyconfigs.addon
    if keyconfig:
        keymaps = keyconfig.keymaps.get('3D View')
        if not keymaps:
            keymaps = keyconfig.keymaps.new(
                name='3D View', space_type='VIEW_3D'
            )
        for operator, key, shift, ctrl, alt in keymap_items_list:
            keymap_item = keymaps.keymap_items.get(operator.bl_idname)
            if not keymap_item:
                keymap_item = keymaps.keymap_items.new(
                    operator.bl_idname,
                    type=key,
                    value='PRESS',
                    shift=shift,
                    ctrl=ctrl,
                    alt=alt,
                    key_modifier='NONE'
                )
                keymap_item.active = True
            addon_hotkeys[operator.bl_idname] = (keymaps, keymap_item)
            has_key = False
            for item in preferences.keymaps_collection:
                if item.operator == operator.bl_idname:
                    has_key = True
            if not has_key:
                key_map_element = preferences.keymaps_collection.add()
                key_map_element.name = operator.bl_label
                key_map_element.operator = operator.bl_idname


def unregister():
    for operator, (keymaps, keymap_item) in addon_hotkeys.items():
        keymaps.keymap_items.remove(keymap_item)
    addon_hotkeys.clear()
