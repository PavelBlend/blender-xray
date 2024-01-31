# standart modules
import os
import time
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


def has_update():
    releases = requests.get(RELEASES_URL)
    releases_list = json.loads(releases.text)
    last_tag_str = releases_list[0]['tag_name']
    last_tag_tuple = last_tag_str[1 : ].split('.')
    last_tag = tuple(map(int, last_tag_tuple))
    current_ver = utils.addon_version
    has_new_release = False
    download_url = None

    if last_tag[0] > current_ver[0]:
        has_new_release = True

    if last_tag[1] > current_ver[1]:
        has_new_release = True

    if last_tag[2] > current_ver[2]:
        has_new_release = True

    if has_new_release:
        download_url = releases_list[0]['assets'][0]['browser_download_url']

    return download_url, last_tag


def check_for_updates():
    download_url, _ = has_update()

    if download_url:
        message = text.get_text(text.warn.new_update_available)
        utils.draw.show_message(
            message,
            (last_tag_str, ),
            text.get_text(text.warn.info_title),
            'INFO',
            operators=[XRAY_OT_install_update.bl_idname, ],
            operators_props=[{'download_url': download_url, }, ]
        )

    else:
        message = text.get_text(text.warn.has_no_update)
        utils.draw.show_message(
            message,
            (),
            text.get_text(text.warn.info_title),
            'INFO'
        )


class XRAY_OT_check_update(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.check_update'
    bl_label = 'Check for Update'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        check_for_updates()
        return {'FINISHED'}


class XRAY_OT_install_update(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.download_update'
    bl_label = 'Download Update?'
    bl_description = 'Download Addon Last Release'

    download_url = bpy.props.StringProperty()
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

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


class XRAY_OT_notify_update(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.notify_update'
    bl_label = 'Notify about Update'
    bl_options = {'REGISTER', 'UNDO'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            current_time = time.time()

            if current_time > self.start_time + 0.01:
                download_url, last_ver = has_update()

                if download_url:
                    ver_text = 'v{0}.{1}.{2}'.format(*last_ver)
                    message = text.get_text(text.warn.new_update_available)
                    report_text = '{0}: {1}'.format(message, ver_text)
                    self.report({'INFO'}, report_text)

                return self.cancel(context)

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self.timer)
        return {'CANCELLED'}

    def execute(self, context):
        self.timer = context.window_manager.event_timer_add(
            0.01,
            window=context.window
        )
        self.start_time = time.time()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


classes = (
    XRAY_OT_check_update,
    XRAY_OT_install_update,
    XRAY_OT_notify_update
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
