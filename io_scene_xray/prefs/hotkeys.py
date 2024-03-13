# blender modules
import bpy

# addon modules
from .. import utils
from .. import formats


keymap_items_list = (
    # operator, key, shift, ctrl, alt
    (formats.obj.imp.ops.XRAY_OT_import_object, 'F5', False, False, False),
    (formats.obj.exp.ops.XRAY_OT_export_object, 'F5', False, False, True),
    (formats.skl.ops.XRAY_OT_import_skls, 'F6', False, False, False),
    (formats.skl.ops.XRAY_OT_export_skls, 'F6', False, False, True),
    (formats.skl.ops.XRAY_OT_export_skl, 'NONE', False, False, False),
    (formats.ogf.imp.ops.XRAY_OT_import_ogf, 'F7', False, False, False),
    (formats.ogf.exp.ops.XRAY_OT_export_ogf, 'F7', False, False, True),
    (formats.omf.ops.XRAY_OT_import_omf, 'F8', False, False, False),
    (formats.omf.ops.XRAY_OT_export_omf, 'F8', False, False, True),
    (formats.anm.ops.XRAY_OT_import_anm, 'F5', False, True, False),
    (formats.anm.ops.XRAY_OT_export_anm, 'F5', False, True, True),
    (formats.bones.ops.XRAY_OT_import_bones, 'F6', False, True, False),
    (formats.bones.ops.XRAY_OT_export_bones, 'F6', False, True, True),
    (formats.dm.ops.XRAY_OT_import_dm, 'F7', False, True, False),
    (formats.dm.ops.XRAY_OT_export_dm, 'F7', False, True, True),
    (formats.details.ops.XRAY_OT_import_details, 'F8', False, True, False),
    (formats.details.ops.XRAY_OT_export_details, 'F8', False, True, True),
    (formats.scene.ops.XRAY_OT_import_scene, 'F5', True, True, False),
    (formats.scene.ops.XRAY_OT_export_scene, 'F5', True, True, True),
    (formats.level.imp.ops.XRAY_OT_import_level, 'F6', True, True, False),
    (formats.level.exp.ops.XRAY_OT_export_level, 'F6', True, True, True),
    (formats.part.ops.XRAY_OT_import_part, 'F7', True, True, False),
    (formats.part.ops.XRAY_OT_export_part, 'F7', True, True, True),
    (formats.group.ops.XRAY_OT_import_group, 'F8', True, True, False),
    (formats.group.ops.XRAY_OT_export_group, 'F8', True, True, True),
    (formats.err.ops.XRAY_OT_import_err, 'NONE', False, False, False),
)


def add_keymaps(only=None):
    pref = utils.version.get_preferences()
    win_manager = bpy.context.window_manager

    if only:
        keyconfig = win_manager.keyconfigs.user
    else:
        keyconfig = win_manager.keyconfigs.addon

    if keyconfig:
        keymaps = keyconfig.keymaps.get('3D View')

        if not keymaps:
            keymaps = keyconfig.keymaps.new(
                name='3D View',
                space_type='VIEW_3D'
            )

        for operator, key, shift, ctrl, alt in keymap_items_list:
            keymap_item = keymaps.keymap_items.get(operator.bl_idname)

            if not keymap_item:
                create = True
                if only is not None:
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
            for item in pref.keymaps_collection:
                if item.operator == operator.bl_idname:
                    has_key = True

            if not has_key:
                key_map_element = pref.keymaps_collection.add()
                key_map_element.name = operator.bl_label
                key_map_element.operator = operator.bl_idname


def register():
    add_keymaps()


def unregister():
    win_manager = bpy.context.window_manager
    keyconfig_addon = win_manager.keyconfigs.addon
    keyconfig_user = win_manager.keyconfigs.user

    for keyconfig in (keyconfig_addon, keyconfig_user):

        if not keyconfig:
            continue

        keymaps = keyconfig.keymaps.get('3D View')

        if not keymaps:
            continue

        for op, _, _, _, _ in keymap_items_list:
            keymap_item = keymaps.keymap_items.get(op.bl_idname)

            if keymap_item:
                keymaps.keymap_items.remove(keymap_item)
