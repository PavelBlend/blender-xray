# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon props
from . import version_utils


def clear_bpy_collection(bpy_collection):
    for prop in bpy_collection:
        bpy_collection.remove(prop)


def remove_bpy_data():
    data = bpy.data
    clear_bpy_collection(data.objects)
    clear_bpy_collection(data.meshes)
    clear_bpy_collection(data.materials)
    clear_bpy_collection(data.textures)
    clear_bpy_collection(data.images)
    clear_bpy_collection(data.armatures)
    clear_bpy_collection(data.actions)


def test_ogf_import(debug_folder):
    file_index = 0
    error_index = 0
    messages_count = 10
    ver_count = 1000
    ver_err_index = 0
    log = []
    log_ver = []
    for root, dirs, files in os.walk(debug_folder):
        for file in files:
            name, ext = os.path.splitext(file)
            ext = ext.lower()
            if ext == '.ogf':
                file_path = os.path.join(root, file)
                file_message = '{0:0>6}: '.format(file_index) + file_path
                file_index += 1
                # if file_index <= 13_800:
                #     continue
                has_error = False
                err_text = None
                try:
                    print(file_message)
                    bpy.ops.xray_import.ogf(
                        directory=root,
                        files=[{'name': file_path}]
                    )
                    remove_bpy_data()
                except Exception as err:
                    err_text = str(err)
                    if not 'Unsupported ogf format version' in err_text:
                        log.append(file_message)
                        log.append(err_text)
                        has_error = True
                        error_index += 1
                    else:
                        log_ver.append(file_message)
                        ver_err_index += 1
                if has_error:
                    print(err_text)
                    print()
                if not error_index % messages_count and error_index:
                    with open('E:\\logs\\errors\\log_{0:0>4}.txt'.format(
                            error_index // messages_count), 'w'
                        ) as file:
                        for message in log:
                            file.write(message + '\n')
                    log.clear()
                if not ver_err_index % ver_count and ver_err_index:
                    with open('E:\\logs\\ver\\log_{0:0>4}.txt'.format(
                                ver_err_index // ver_count
                        ), 'w') as file:
                        for message in log_ver:
                            file.write(message + '\n')
                    log_ver.clear()


op_props = {
    'directory': bpy.props.StringProperty(
        subtype="DIR_PATH", options={'SKIP_SAVE'}
    ),
}


class XRAY_OT_test_ogf_import(
        bpy.types.Operator,
        bpy_extras.io_utils.ImportHelper
    ):
    bl_idname = 'io_scene_xray.test_ogf_import'
    bl_label = 'Test OGF Import'
    bl_options = {'REGISTER'}

    def execute(self, context):
        test_ogf_import(self.directory)
        return {'FINISHED'}

    def invoke(self, context, event):
        return super().invoke(context, event)


def register():
    version_utils.assign_props([(op_props, XRAY_OT_test_ogf_import), ])
    bpy.utils.register_class(XRAY_OT_test_ogf_import)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_test_ogf_import)
