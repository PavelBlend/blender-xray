import bpy

from .obj.imp.ops import OpImportObject
from .obj.exp.ops import OpExportObject


class KayMap():
    def __init__(self):
        self.key = None
        self.text = None
        self.operator_id = None
        self.shift = False
        self.ctrl = False
        self.alt = False
        self.key_modifier = 'NONE'


io_scene_xray_keymaps = {}

# keymaps

# import object
obj_imp_keymap = KayMap()
obj_imp_keymap.key = 'F8'
obj_imp_keymap.operator_id = OpImportObject.bl_idname
obj_imp_keymap.text = OpImportObject.bl_label

# export object
obj_exp_keymap = KayMap()
obj_exp_keymap.key = 'F8'
obj_exp_keymap.operator_id = OpExportObject.bl_idname
obj_exp_keymap.text = OpExportObject.bl_label
obj_exp_keymap.shift = True

keymaps_list = [
    obj_imp_keymap,
    obj_exp_keymap
]


def create_keymap(keymaps, keymap):
    keymap_item = keymaps.keymap_items.new(
        keymap.operator_id,
        type=keymap.key,
        value='PRESS',
        shift=keymap.shift,
        ctrl=keymap.ctrl,
        alt=keymap.alt,
        key_modifier=keymap.key_modifier
    )
    io_scene_xray_keymaps[keymap.operator_id] = (keymaps, keymap_item)


def register_hotkeys():
    win_manager = bpy.context.window_manager
    addon_keyconfigs = win_manager.keyconfigs.addon
    if addon_keyconfigs:
        keymaps = addon_keyconfigs.keymaps.new(
            name='3D View', space_type='VIEW_3D'
        )
        for keymap in keymaps_list:
            create_keymap(keymaps, keymap)


def unregister_hotkeys():
    for operator_id, (keymaps, keymap_item) in io_scene_xray_keymaps.items():
        keymaps.keymap_items.remove(keymap_item)
    io_scene_xray_keymaps.clear()
