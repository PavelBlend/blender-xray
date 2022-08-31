# standart modules
import os
import time

# blender modules
import bpy
import bpy_extras
import mathutils

# addon modules
from . import utils


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


op_modal_props = {
    'test_folder': bpy.props.StringProperty(),
    'pause': bpy.props.FloatProperty(default=0.1, min=0.0001, max=100.0)
}


class XRAY_OT_test_ogf_import_modal(bpy.types.Operator):
    bl_idname = 'wm.test_ogf_import_modal'
    bl_label = 'Test OGF Import Modal'
    bl_options = {'REGISTER'}

    timer = None
    last_time = 0

    if not utils.version.IS_28:
        for prop_name, prop_value in op_modal_props.items():
            exec('{0} = op_modal_props.get("{0}")'.format(prop_name))

    def collect_files(self, context):
        self.file_index = 0
        self.error_index = 0
        self.messages_count = 10
        self.ver_count = 1000
        self.ver_err_index = 0
        self.log = []
        self.log_ver = []
        self.files_list = []
        for root, dirs, files in os.walk(self.test_folder):
            for file in files:
                name, ext = os.path.splitext(file)
                ext = ext.lower()
                if ext == '.ogf':
                    self.files_list.append((root, file))
        return {'FINISHED'}

    def test_ogf_import(self):
        remove_bpy_data()
        root, file = self.files_list[self.file_index]
        file_path = os.path.join(root, file)
        file_message = '{0:0>6}: '.format(self.file_index) + file_path
        self.file_index += 1
        has_error = False
        err_text = None
        try:
            print(file_message)
            bpy.ops.xray_import.ogf(
                directory=root,
                files=[{'name': file}],
                import_motions=False
            )
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    ctx = bpy.context.copy()
                    ctx['area'] = area
                    ctx['region'] = area.regions[-1]
                    bpy.ops.view3d.view_all(ctx, center=False)
                    bbox_min_x = 1000000.0
                    bbox_min_y = 1000000.0
                    bbox_min_z = 1000000.0
                    bbox_max_x = -1000000.0
                    bbox_max_y = -1000000.0
                    bbox_max_z = -1000000.0
                    for obj in bpy.data.objects:
                        min_bbox = mathutils.Vector(obj.bound_box[0])
                        max_bbox = mathutils.Vector(obj.bound_box[6])
                        bbox_min_x = min(bbox_min_x, min_bbox.x)
                        bbox_min_y = min(bbox_min_y, min_bbox.y)
                        bbox_min_z = min(bbox_min_z, min_bbox.z)
                        bbox_max_x = max(bbox_max_x, min_bbox.x)
                        bbox_max_y = max(bbox_max_y, min_bbox.y)
                        bbox_max_z = max(bbox_max_z, min_bbox.z)
                    dim_all_x = bbox_max_x - bbox_min_x
                    dim_all_y = bbox_max_y - bbox_min_y
                    dim_all_z = bbox_max_z - bbox_min_z
                    dim_max = max(dim_all_x, dim_all_y, dim_all_z)
                    clip_end = max(500.0, dim_max * 10)
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            if self.clip_end is None:
                                self.clip_end = space.clip_end
                            space.clip_end = clip_end
        except Exception as err:
            err_text = str(err)
            if not 'Unsupported ogf format version' in err_text:
                self.log.append(file_message)
                self.log.append(err_text)
                has_error = True
                self.error_index += 1
            else:
                self.log_ver.append(file_message)
                self.ver_err_index += 1
        if has_error:
            print(err_text)
            print()
        if not self.error_index % self.messages_count and self.error_index:
            with open('E:\\logs\\errors\\log_{0:0>4}.txt'.format(
                    self.error_index // self.messages_count), 'w'
                ) as file:
                for message in self.log:
                    file.write(message + '\n')
            self.log.clear()
        if not self.ver_err_index % self.ver_count and self.ver_err_index:
            with open('E:\\logs\\ver\\log_{0:0>4}.txt'.format(
                        self.ver_err_index // self.ver_count
                ), 'w') as file:
                for message in self.log_ver:
                    file.write(message + '\n')
            self.log_ver.clear()

    def set_clip_end(self):
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.clip_end = self.clip_end

    def modal(self, context, event):
        if event.type == 'TIMER':
            if self.last_time + self.pause < time.time():
                if self.file_index < len(self.files_list):
                    self.test_ogf_import()
                else:
                    context.window_manager.event_timer_remove(self.timer)
                    remove_bpy_data()
                    self.set_clip_end()
                    return {'FINISHED'}
                self.last_time = time.time()
        elif event.type == 'ESC':
            remove_bpy_data()
            self.set_clip_end()
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def execute(self, context):
        self.last_time = time.time()
        self.clip_end = None
        self.collect_files(context)
        self.timer = context.window_manager.event_timer_add(
            self.pause,
            window=context.window
        )
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


op_props = {
    'directory': bpy.props.StringProperty(
        subtype="DIR_PATH", options={'SKIP_SAVE', 'HIDDEN'}
    ),
    'pause': bpy.props.FloatProperty(
        default=0.1,
        min=0.0001,
        max=100.0,
        name='Pause'
    )
}


class XRAY_OT_test_ogf_import(
        bpy.types.Operator,
        bpy_extras.io_utils.ImportHelper
    ):
    bl_idname = 'io_scene_xray.test_ogf_import'
    bl_label = 'Test OGF Import'
    bl_options = {'REGISTER'}

    if not utils.version.IS_28:
        for prop_name, prop_value in op_props.items():
            exec('{0} = op_props.get("{0}")'.format(prop_name))

    def execute(self, context):
        bpy.ops.wm.test_ogf_import_modal(
            test_folder=self.directory,
            pause=self.pause
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        return super().invoke(context, event)


def register():
    utils.version.assign_props([(op_props, XRAY_OT_test_ogf_import), ])
    bpy.utils.register_class(XRAY_OT_test_ogf_import)
    utils.version.assign_props([(op_modal_props, XRAY_OT_test_ogf_import_modal), ])
    bpy.utils.register_class(XRAY_OT_test_ogf_import_modal)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_test_ogf_import)
    bpy.utils.unregister_class(XRAY_OT_test_ogf_import_modal)
