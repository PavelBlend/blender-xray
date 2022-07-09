# blender modules
import bpy

# addon modules
from . import version_utils

# plugin modules
from . import anm
from . import bones
from . import details
from . import dm
from . import err
from . import level
from . import obj
from . import ogf
from . import omf
from . import scene
from . import skl
from . import part


keymap_items_list = (
    # operator, key, shift, ctrl, alt
    (obj.imp.ops.XRAY_OT_import_object, 'F5', False, False, False),
    (obj.exp.ops.XRAY_OT_export_object, 'F5', False, False, True),
    (skl.ops.XRAY_OT_import_skls, 'F6', False, False, False),
    (skl.ops.XRAY_OT_export_skls, 'F6', False, False, True),
    (ogf.ops.XRAY_OT_import_ogf, 'F7', False, False, False),
    (ogf.ops.XRAY_OT_export_ogf, 'F7', False, False, True),
    (omf.ops.XRAY_OT_import_omf, 'F8', False, False, False),
    (omf.ops.XRAY_OT_export_omf, 'F8', False, False, True),
    (anm.ops.XRAY_OT_import_anm, 'F5', False, True, False),
    (anm.ops.XRAY_OT_export_anm, 'F5', False, True, True),
    (bones.ops.XRAY_OT_import_bones, 'F6', False, True, False),
    (bones.ops.XRAY_OT_export_bones, 'F6', False, True, True),
    (dm.ops.XRAY_OT_import_dm, 'F7', False, True, False),
    (dm.ops.XRAY_OT_export_dm, 'F7', False, True, True),
    (details.ops.XRAY_OT_import_details, 'F8', False, True, False),
    (details.ops.XRAY_OT_export_details, 'F8', False, True, True),
    (scene.ops.XRAY_OT_import_scene_selection, 'F5', True, True, False),
    (scene.ops.XRAY_OT_export_scene_selection, 'F5', True, True, True),
    (level.ops.XRAY_OT_import_level, 'F6', True, True, False),
    (level.ops.XRAY_OT_export_level, 'F6', True, True, True),
    (part.ops.XRAY_OT_import_part, 'F7', True, True, False),
    (err.ops.XRAY_OT_import_err, 'F8', True, True, False)
)


def add_keymaps(only=None):
    preferences = version_utils.get_preferences()
    win_manager = bpy.context.window_manager
    if only:
        keyconfig = win_manager.keyconfigs.user
    else:
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
                create = True
                if not only is None:
                    if only != operator.bl_idname:
                        create = False
                if create:
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
            has_key = False
            for item in preferences.keymaps_collection:
                if item.operator == operator.bl_idname:
                    has_key = True
            if not has_key:
                key_map_element = preferences.keymaps_collection.add()
                key_map_element.name = operator.bl_label
                key_map_element.operator = operator.bl_idname


def register():
    add_keymaps()


def unregister():
    win_manager = bpy.context.window_manager
    keyconfig_addon = win_manager.keyconfigs.addon
    keyconfig_user = win_manager.keyconfigs.user
    for keyconfig in (keyconfig_addon, keyconfig_user):
        if keyconfig:
            keymaps = keyconfig.keymaps.get('3D View')
            if keymaps:
                for op, _, _, _, _ in keymap_items_list:
                    keymap_item = keymaps.keymap_items.get(op.bl_idname)
                    if keymap_item:
                        keymaps.keymap_items.remove(keymap_item)
