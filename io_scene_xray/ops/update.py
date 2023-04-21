# standart modules
import os
import shutil
import json
import requests
import tempfile
import zipfile

# blender modules
import bpy

# addon modules
from .. import text
from .. import utils


RELEASES_URL = 'https://api.github.com/repos/PavelBlend/blender-xray/releases'


def check_for_updates():
    releases = requests.get(RELEASES_URL)
    releases_list = json.loads(releases.text)
    last_tag_str = releases_list[0]['tag_name']
    last_tag_tuple = last_tag_str[1 : ].split('.')
    last_tag = tuple(map(int, last_tag_tuple))
    current_ver = utils.addon_version
    has_new_release = False
    if last_tag[0] > current_ver[0]:
        has_new_release = True
    if last_tag[1] > current_ver[1]:
        has_new_release = True
    if last_tag[2] > current_ver[2]:
        has_new_release = True
    if has_new_release:
        download_url = releases_list[0]['assets'][0]['browser_download_url']
        message = text.get_text(text.warn.new_update_available).capitalize()
        utils.draw.show_message(
            message,
            (last_tag_str, ),
            text.get_text(text.warn.info_title).capitalize(),
            'INFO',
            operator=XRAY_OT_install_update.bl_idname,
            operator_props={'download_url': download_url, }
        )
    else:
        message = text.get_text(text.warn.has_no_update).capitalize()
        utils.draw.show_message(
            message,
            (),
            text.get_text(text.warn.info_title).capitalize(),
            'INFO'
        )


class XRAY_OT_check_update(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.check_update'
    bl_label = 'Check for Update'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        check_for_updates()
        return {'FINISHED'}


op_props = {
    'download_url': bpy.props.StringProperty(),
}


class XRAY_OT_install_update(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.download_update'
    bl_label = 'Download Update?'
    bl_description = 'Download Addon Last Release'

    props = op_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def execute(self, context):
        addon_zip_file = requests.get(self.download_url)
        directory = tempfile.gettempdir()
        file_name = self.download_url.split('/')[-1]
        file_path = os.path.join(directory, file_name)
        with open(file_path, 'wb') as file:
            file.write(addon_zip_file.content)
        addon_dir = os.path.dirname(os.path.dirname(__file__))
        shutil.rmtree(addon_dir)
        addons_dir = os.path.dirname(addon_dir)
        with zipfile.ZipFile(file_path) as file:
            file.extractall(addons_dir)
        os.remove(file_path)
        self.report({'INFO'}, 'Installed!')
        return {'FINISHED'}


classes = (XRAY_OT_check_update, XRAY_OT_install_update)


def register():
    utils.version.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
