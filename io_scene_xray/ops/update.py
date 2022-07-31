# standart modules
import json
import requests

# blender modules
import bpy

# addon modules
from .. import text
from .. import draw_utils
from .. import bl_info


RELEASES_URL = 'https://api.github.com/repos/PavelBlend/blender-xray/releases'


def check_for_updates():
    try:
        releases = requests.get(RELEASES_URL)
    except:
        return
    releases_list = json.loads(releases.text)
    last_tag_str = releases_list[0]['tag_name']
    last_tag_tuple = last_tag_str[1 : ].split('.')
    last_tag = tuple(map(int, last_tag_tuple))
    current_ver = bl_info['version']
    has_new_release = False
    if last_tag[0] > current_ver[0]:
        has_new_release = True
    if last_tag[1] > current_ver[1]:
        has_new_release = True
    if last_tag[2] > current_ver[2]:
        has_new_release = True
    if has_new_release:
        message = text.get_text(text.warn.new_update_available).capitalize()
        draw_utils.show_message(
            message,
            (last_tag_str, ),
            text.get_text(text.warn.info_title).capitalize(),
            'INFO'
        )


class XRAY_OT_check_update(bpy.types.Operator):
    bl_idname = 'io_scene_xray.check_update'
    bl_label = 'Check for Update'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        check_for_updates()
        return {'FINISHED'}


def register():
    bpy.utils.register_class(XRAY_OT_check_update)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_check_update)
