# standart modules
import os
import time

# blender modules
import bpy
import mathutils

# addon modules
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
    clear_bpy_collection(data.texts)


op_props = {
    'directory': bpy.props.StringProperty(
        subtype='DIR_PATH',
        options={'SKIP_SAVE', 'HIDDEN'}
    ),
    'pause': bpy.props.FloatProperty(
        default=0.1,
        min=0.0001,
        max=100.0,
        precision=4,
        name='Pause'
    ),
    'import_object': bpy.props.BoolProperty(name='Object', default=True),
    'import_ogf': bpy.props.BoolProperty(name='Ogf', default=True),
    'import_dm': bpy.props.BoolProperty(name='Dm', default=True),
    'import_details': bpy.props.BoolProperty(name='Details', default=True),
    'import_motions': bpy.props.BoolProperty(
        name='Import Motions',
        default=False
    ),
    'min_size': bpy.props.IntProperty(default=0, min=0, max=2**31-1),
    'max_size': bpy.props.IntProperty(
        default=1_000_000_000,
        min=0,
        max=2**31-1
    )
}


class XRAY_OT_test_import_modal(bpy.types.Operator):
    bl_idname = 'io_scene_xray.test_import_modal'
    bl_label = 'Test Import Modal'
    bl_options = {'REGISTER'}

    timer = None
    last_time = 0

    if not utils.version.IS_28:
        for prop_name, prop_value in op_props.items():
            exec('{0} = op_props.get("{0}")'.format(prop_name))

    def collect_files(self, context):
        self.file_index = 0
        self.files_list = []
        for root, dirs, files in os.walk(self.directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                if not (self.min_size < file_size < self.max_size):
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
        file_message = '{0:0>6}: '.format(self.file_index) + file_path
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
            min_bbox = mathutils.Vector(obj.bound_box[0])
            max_bbox = mathutils.Vector(obj.bound_box[6])

            bbox_min_x = min(bbox_min_x, min_bbox.x)
            bbox_min_y = min(bbox_min_y, min_bbox.y)
            bbox_min_z = min(bbox_min_z, min_bbox.z)

            bbox_max_x = max(bbox_max_x, min_bbox.x)
            bbox_max_y = max(bbox_max_y, min_bbox.y)
            bbox_max_z = max(bbox_max_z, min_bbox.z)

        dim_x = bbox_max_x - bbox_min_x
        dim_y = bbox_max_y - bbox_min_y
        dim_z = bbox_max_z - bbox_min_z

        dim_max = max(dim_x, dim_y, dim_z)
        clip_end = max(500.0, dim_max * 10)

        return clip_end

    def set_view(self):
        clip_end = self.calc_clip_end()

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                ctx = bpy.context.copy()
                ctx['area'] = area
                ctx['region'] = area.regions[-1]
                bpy.ops.view3d.view_all(ctx, center=False)

                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.clip_end = clip_end

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
                else:
                    return self.cancel(context)
                self.last_time = time.time()

        elif event.type == 'ESC':
            return self.cancel(context)

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self.timer)
        remove_bpy_data()
        self.set_clip_end(self.clip_end_old)
        return {'CANCELLED'}

    def execute(self, context):
        space_3d = self.get_space_3d()
        self.clip_end_old = space_3d.clip_end

        self.collect_files(context)
        self.last_time = time.time()

        self.timer = context.window_manager.event_timer_add(
            self.pause,
            window=context.window
        )
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}


class XRAY_OT_test_import(bpy.types.Operator):
    bl_idname = 'io_scene_xray.test_import'
    bl_label = 'Test Import'
    bl_options = {'REGISTER'}

    if not utils.version.IS_28:
        for prop_name, prop_value in op_props.items():
            exec('{0} = op_props.get("{0}")'.format(prop_name))

    def draw(self, context):
        lay = self.layout
        lay.prop(self, 'pause')

        lay.label(text='Formats:')

        row = lay.row()
        row.prop(self, 'import_object')
        row.prop(self, 'import_ogf')

        row = lay.row()
        row.prop(self, 'import_dm')
        row.prop(self, 'import_details')

        lay.label(text='Options:')
        lay.prop(self, 'import_motions')

        lay.label(text='Filters:')
        lay.label(text='Skip Files by File Size (Size in Bytes)')
        lay.prop(self, 'min_size', text='Min Size')
        lay.prop(self, 'max_size', text='Max Size')

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
            max_size=self.max_size
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


classes = (
    (XRAY_OT_test_import, op_props),
    (XRAY_OT_test_import_modal, op_props)
)


def register():
    for clas, props in classes:
        utils.version.assign_props([(props, clas), ])
        bpy.utils.register_class(clas)


def unregister():
    for clas, props in reversed(classes):
        bpy.utils.unregister_class(clas)
