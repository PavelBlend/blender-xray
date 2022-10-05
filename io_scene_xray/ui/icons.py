# standart modules
import os

# blender modules
import bpy


preview_collections = {}
ICON_EXT = 'png'
STALKER_ICON_NAME = 'stalker'


def get_stalker_icon():
    pcoll = preview_collections['main']
    icon = pcoll[STALKER_ICON_NAME]
    # without this line in some cases the icon is not visible
    len(icon.icon_pixels)
    return icon.icon_id


def register():
    # load icon
    pcoll = bpy.utils.previews.new()
    module_dir = os.path.dirname(__file__)
    addon_dir = os.path.dirname(module_dir)
    icons_dir = os.path.join(addon_dir, 'ui')
    icon_file = STALKER_ICON_NAME + os.extsep + ICON_EXT
    icon_path = os.path.join(icons_dir, icon_file)
    pcoll.load(STALKER_ICON_NAME, icon_path, 'IMAGE')
    preview_collections['main'] = pcoll


def unregister():
    # remove icon
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
