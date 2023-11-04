# standart modules
import os
import time

# blender modules
import bpy
import mathutils

# addon modules
from .. import log
from .. import utils


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


FORMAT_FULL = '%Y.%m.%d %H:%M'
FORMAT_SHORT = '%Y.%m.%d'


def get_float_time_by_str(time_str):
    try:
        struct_time = time.strptime(time_str, FORMAT_FULL)
        float_time = time.mktime(struct_time)
    except:
        try:
            struct_time = time.strptime(time_str, FORMAT_SHORT)
            float_time = time.mktime(struct_time)
        except:
            float_time = None
    return float_time


def update_time(self, context):
    for prop_name in ('time_min', 'time_max'):
        time_str = getattr(self, prop_name)
        if time_str:
            float_time = get_float_time_by_str(time_str)
            if float_time is None:
                setattr(self, prop_name, '')


class XRAY_OT_test_import_modal(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.test_import_modal'
    bl_label = 'Test Import Modal'
    bl_options = {'REGISTER'}

    timer = None
    last_time = 0

    directory = bpy.props.StringProperty(
        subtype='DIR_PATH',
        options={'SKIP_SAVE', 'HIDDEN'}
    )
    pause = bpy.props.FloatProperty(
        default=0.1,
        min=0.0001,
        max=100.0,
        precision=4,
        name='Pause'
    )
    import_object = bpy.props.BoolProperty(name='Object', default=True)
    import_ogf = bpy.props.BoolProperty(name='Ogf', default=True)
    import_dm = bpy.props.BoolProperty(name='Dm', default=True)
    import_details = bpy.props.BoolProperty(name='Details', default=True)
    import_motions = bpy.props.BoolProperty(
        name='Import Motions',
        default=False
    )
    min_size = bpy.props.IntProperty(default=0, min=0, max=2**31-1)
    max_size = bpy.props.IntProperty(
        default=2**31-1,
        min=0,
        max=2**31-1
    )
    time_min = bpy.props.StringProperty(update=update_time)
    time_max = bpy.props.StringProperty(update=update_time)

    def collect_files(self, context):
        self.file_index = 0
        self.files_list = []

        min_time_float = get_float_time_by_str(self.time_min)
        max_time_float = get_float_time_by_str(self.time_max)

        for root, dirs, files in os.walk(self.directory):
            for file in files:
                file_path = os.path.join(root, file)

                file_size = os.path.getsize(file_path)
                if not self.min_size < file_size < self.max_size:
                    continue

                date_float = os.path.getmtime(file_path)

                if not min_time_float is None:
                    if date_float < min_time_float:
                        continue

                if not max_time_float is None:
                    if date_float > max_time_float:
                        continue

                name, ext = os.path.splitext(file)
                ext = ext.lower()

                if ext == '.object' and self.import_object:
                    skip = False
                elif ext == '.ogf' and self.import_ogf:
                    skip = False
                elif ext == '.dm' and self.import_dm:
                    skip = False
                elif ext == '.details' and self.import_details:
                    skip = False
                else:
                    skip = True

                if not skip:
                    self.files_list.append((root, file, file_path))

    def test_import(self):
        remove_bpy_data()
        root, file, file_path = self.files_list[self.file_index]
        ext = os.path.splitext(file)[-1]
        file_message = '{0:0>6}: {1}'.format(self.file_index, file_path)
        self.file_index += 1

        try:
            print(file_message)
            if ext == '.object':
                bpy.ops.xray_import.object(
                    directory=root,
                    files=[{'name': file}],
                    import_motions=self.import_motions
                )
            elif ext == '.ogf':
                bpy.ops.xray_import.ogf(
                    directory=root,
                    files=[{'name': file}],
                    import_motions=self.import_motions
                )
            elif ext == '.dm':
                bpy.ops.xray_import.dm(
                    directory=root,
                    files=[{'name': file}]
                )
            elif ext == '.details':
                bpy.ops.xray_import.details(
                    directory=root,
                    files=[{'name': file}],
                    load_slots=False
                )
            self.set_view()

        except BaseException as err:
            print(str(err))

    def calc_clip_end(self):
        bbox_min_x = 1000000.0
        bbox_min_y = 1000000.0
        bbox_min_z = 1000000.0

        bbox_max_x = -1000000.0
        bbox_max_y = -1000000.0
        bbox_max_z = -1000000.0

        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue

            min_bbox = mathutils.Vector(obj.bound_box[0])
            max_bbox = mathutils.Vector(obj.bound_box[6])

            bbox_min_x = min(bbox_min_x, min_bbox.x)
            bbox_min_y = min(bbox_min_y, min_bbox.y)
            bbox_min_z = min(bbox_min_z, min_bbox.z)

            bbox_max_x = max(bbox_max_x, max_bbox.x)
            bbox_max_y = max(bbox_max_y, max_bbox.y)
            bbox_max_z = max(bbox_max_z, max_bbox.z)

        dim_x = bbox_max_x - bbox_min_x
        dim_y = bbox_max_y - bbox_min_y
        dim_z = bbox_max_z - bbox_min_z

        dim_max = max(dim_x, dim_y, dim_z)
        clip_end = max(500.0, dim_max * 4)

        return clip_end

    def set_view(self):
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                utils.version.select_object(obj)

        clip_end = self.calc_clip_end()

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                ctx = bpy.context.copy()
                ctx['area'] = area
                ctx['region'] = area.regions[-1]
                bpy.ops.view3d.view_selected(ctx)

                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.clip_end = clip_end

        bpy.ops.object.select_all(action='DESELECT')

    def get_space_3d(self):
        space_3d = None
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space_3d = space
        return space_3d

    def set_clip_end(self, clip_end):
        space_3d = self.get_space_3d()
        if space_3d:
            space_3d.clip_end = clip_end

    def modal(self, context, event):
        if event.type == 'TIMER':
            cur_time = time.time()
            if cur_time > self.last_time + self.pause or not self.file_index:
                if self.file_index < len(self.files_list):
                    self.test_import()
                    self.last_time = time.time()
                else:
                    return self.cancel(context)

        elif event.type == 'ESC':
            return self.cancel(context)

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self.timer)
        remove_bpy_data()

        log.general_log.flush(is_last_flush=True)
        log.general_log = None

        self.set_clip_end(self.clip_end_old)
        bpy.ops.view3d.view_axis(type='TOP')
        return {'CANCELLED'}

    @log.execute_with_logger
    def execute(self, context):
        space_3d = self.get_space_3d()
        self.clip_end_old = space_3d.clip_end

        self.collect_files(context)
        self.last_time = time.time()

        log.general_log = log.Logger(self.report)

        self.timer = context.window_manager.event_timer_add(
            self.pause,
            window=context.window
        )
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}


class XRAY_OT_test_import(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.test_import'
    bl_label = 'Test Import'
    bl_options = {'REGISTER'}

    directory = bpy.props.StringProperty(
        subtype='DIR_PATH',
        options={'SKIP_SAVE', 'HIDDEN'}
    )
    pause = bpy.props.FloatProperty(
        default=0.1,
        min=0.0001,
        max=100.0,
        precision=4,
        name='Pause'
    )
    import_object = bpy.props.BoolProperty(name='Object', default=True)
    import_ogf = bpy.props.BoolProperty(name='Ogf', default=True)
    import_dm = bpy.props.BoolProperty(name='Dm', default=True)
    import_details = bpy.props.BoolProperty(name='Details', default=True)
    import_motions = bpy.props.BoolProperty(
        name='Import Motions',
        default=False
    )
    min_size = bpy.props.IntProperty(default=0, min=0, max=2**31-1)
    max_size = bpy.props.IntProperty(
        default=2**31-1,
        min=0,
        max=2**31-1
    )
    time_min = bpy.props.StringProperty(update=update_time)
    time_max = bpy.props.StringProperty(update=update_time)

    def draw(self, context):    # pragma: no cover
        lay = self.layout
        lay.prop(self, 'pause')

        box = lay.box()
        box.label(text='Formats:')

        row = box.row()
        row.prop(self, 'import_object')
        row.prop(self, 'import_ogf')

        row = box.row()
        row.prop(self, 'import_dm')
        row.prop(self, 'import_details')

        box = lay.box()
        box.label(text='Options:')
        box.prop(self, 'import_motions')

        lay.label(text='Filters:')

        box = lay.box()
        box.label(text='Skip Files by Size:')
        box.prop(self, 'min_size', text='Min')
        box.prop(self, 'max_size', text='Max')
        box.label(text='Size in Bytes', icon='INFO')

        box = lay.box()
        box.label(text='Skip Files by Creation Date:')

        row = box.row()
        box.prop(self, 'time_min', text='Min')
        box.prop(self, 'time_max', text='Max')

        box.label(text='Time Formats:', icon='INFO')
        box.label(text='Year.Month.Day Hours:Minutes')
        box.label(text='Year.Month.Day')

    def execute(self, context):
        bpy.ops.io_scene_xray.test_import_modal(
            directory=self.directory,
            pause=self.pause,
            import_object=self.import_object,
            import_ogf=self.import_ogf,
            import_dm=self.import_dm,
            import_details=self.import_details,
            import_motions=self.import_motions,
            min_size=self.min_size,
            max_size=self.max_size,
            time_min=self.time_min,
            time_max=self.time_max
        )
        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


classes = (
    XRAY_OT_test_import,
    XRAY_OT_test_import_modal
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
