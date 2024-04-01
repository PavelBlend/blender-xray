# standart modules
import os

# blender modules
import bpy

# addon modules
from .. import utils


ICON_EXT = 'png'


def register():
    # get icon file path
    ui_package_dir = os.path.dirname(__file__)
    icon_file = utils.draw.STALKER_ICON_NAME + os.extsep + ICON_EXT
    icon_path = os.path.join(ui_package_dir, icon_file)

    # load icon
    pcoll = bpy.utils.previews.new()
    pcoll.load(utils.draw.STALKER_ICON_NAME, icon_path, 'IMAGE')
    utils.draw.preview_collections['main'] = pcoll


def unregister():
    # remove icon
    for pcoll in utils.draw.preview_collections.values():
        bpy.utils.previews.remove(pcoll)

    utils.draw.preview_collections.clear()
