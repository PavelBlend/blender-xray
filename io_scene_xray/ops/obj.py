# standart modules
import zlib

# blender modules
import bpy
import mathutils

# addon modules
from .. import utils
from .. import text


class XRAY_OT_place_objects(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.place_objects'
    bl_label = 'Place Selected Objects'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    plane = bpy.props.EnumProperty(
        name='Plane',
        default='XY',
        items=(
            ('XY', 'XY', ''),
            ('XZ', 'XZ', ''),
            ('YZ', 'YZ', '')
        )
    )
    rows = bpy.props.IntProperty(name='Rows', default=1, min=1, max=1000)
    offset_h = bpy.props.FloatProperty(
        name='Horizontal Offset',
        default=2.0,
        min=0.001
    )
    offset_v = bpy.props.FloatProperty(
        name='Vertical Offset',
        default=2.0,
        min=0.001
    )

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Plane:')
        row = column.row(align=True)
        row.prop(self, 'plane', expand=True)
        column.prop(self, 'rows')
        column.prop(self, 'offset_h')
        column.prop(self, 'offset_v')

    @utils.set_cursor_state
    def execute(self, context):
        objs = set()
        for obj in context.selected_objects:
            if obj.xray.isroot:
                objs.add(obj.name)
        objs = sorted(list(objs))
        objects_count = len(objs)
        column = 0
        row = 0
        objects_in_row = objects_count // self.rows
        if (objects_count % self.rows) == 0:
            offset = 1
        else:
            offset = 0
        for obj_name in objs:
            obj = bpy.data.objects.get(obj_name)
            if self.plane == 'XY':
                obj.location.x = column * self.offset_h
                obj.location.y = row * self.offset_v
                obj.location.z = 0.0
            elif self.plane == 'XZ':
                obj.location.x = column * self.offset_h
                obj.location.y = 0.0
                obj.location.z = row * self.offset_v
            else:
                obj.location.x = 0.0
                obj.location.y = column * self.offset_h
                obj.location.z = row * self.offset_v
            if ((column + offset) % objects_in_row) == 0 and column != 0:
                column = 0
                row += 1
            else:
                column += 1
        utils.draw.redraw_areas()
        self.report({'INFO'}, 'Moved {0} objects'.format(objects_count))
        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_colorize_objects(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.colorize_objects'
    bl_label = 'Colorize Objects'
    bl_description = 'Set a pseudo-random object color'
    bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.EnumProperty(
        default='SELECTED_OBJECTS',
        items=(
            ('ACTIVE_OBJECT', 'Active Object', ''),
            ('SELECTED_OBJECTS', 'Selected Objects', ''),
            ('ALL_OBJECTS', 'All Objects', '')
        )
    )
    color_mode = bpy.props.EnumProperty(
        default='RANDOM_BY_OBJECT',
        items=(
            ('RANDOM_BY_MESH', 'Random by Mesh', ''),
            ('RANDOM_BY_OBJECT', 'Random by Object', ''),
            ('RANDOM_BY_ROOT', 'Random by Root', ''),
            ('SINGLE_COLOR', 'Single Color', '')
        )
    )
    seed = bpy.props.IntProperty(min=0, max=255)
    power = bpy.props.FloatProperty(default=0.5, min=0.0, max=1.0)
    color = bpy.props.FloatVectorProperty(
        default=(0.5, 0.5, 0.5, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        column = layout.column(align=True)

        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

        column.label(text='Color Mode:')
        column.prop(self, 'color_mode', expand=True)

        column_settings = column.column(align=True)
        column_settings.active = self.color_mode != 'SINGLE_COLOR'

        column_settings.label(text='Settings:')
        column_settings.prop(self, 'seed', text='Seed')
        column_settings.prop(self, 'power', text='Power', slider=True)

        column_color = column.column(align=True)
        column_color.active = self.color_mode == 'SINGLE_COLOR'
        column_color.prop(self, 'color', text='Color')

    @utils.set_cursor_state
    def execute(self, context):
        # active object
        if self.mode == 'ACTIVE_OBJECT':
            obj = context.active_object
            if not obj:
                self.report({'ERROR'}, 'No active object')
                return {'CANCELLED'}
            objects = (obj, )

        # selected objects
        elif self.mode == 'SELECTED_OBJECTS':
            objects = context.selected_objects
            if not objects:
                self.report({'ERROR'}, 'No objects selected')
                return {'CANCELLED'}

        # all objects
        else:
            objects = bpy.data.objects
            if not objects:
                self.report({'ERROR'}, 'Blend-file has no objects')
                return {'CANCELLED'}

        # colorize
        changed_objects_count = 0
        for obj in objects:
            if obj.type != 'MESH':
                continue

            if self.color_mode == 'RANDOM_BY_MESH':
                name = obj.data.name
            elif self.color_mode == 'RANDOM_BY_OBJECT':
                name = obj.name
            elif self.color_mode == 'RANDOM_BY_ROOT':
                root = utils.obj.find_root(obj)
                name = root.name
            else:
                name = None

            if name is None:
                color = list(self.color)
            else:
                data = bytearray(name, 'utf8')
                data.append(self.seed)
                hsh = zlib.crc32(data)
                color = mathutils.Color()
                color.hsv = (
                    (hsh & 0xFF) / 0xFF,
                    (((hsh >> 8) & 3) / 3 * 0.5 + 0.5) * self.power,
                    ((hsh >> 2) & 1) * (0.5 * self.power) + 0.5
                )
                color = [color.r, color.g, color.b, 1.0]

            obj.color = color
            changed_objects_count += 1

        utils.draw.redraw_areas()
        self.report(
            {'INFO'},
            'Changed {} object(s)'.format(changed_objects_count)
        )

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_set_export_path(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.set_export_path'
    bl_label = 'Set Export Path'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    directory = bpy.props.StringProperty(
        subtype='DIR_PATH',
        options={'SKIP_SAVE'}
    )
    mode = bpy.props.EnumProperty(
        default='ACTIVE_OBJECT',
        items=(
            ('ACTIVE_OBJECT', 'Active Object', ''),
            ('SELECTED_OBJECTS', 'Selected Objects', ''),
            ('ALL_OBJECTS', 'All Objects', '')
        )
    )

    def _get_folders(self):
        objects_folders = utils.ie.get_pref_paths('objects_folder')

        objs_folder = None
        for val in objects_folders:
            if val:
                objs_folder = val

        meshes_folder = utils.ie.get_pref_paths('meshes_folder')

        mshs_folder = None
        for val in meshes_folder:
            if val:
                mshs_folder = val

        return objs_folder, mshs_folder

    def _get_objs(self):
        objs = []

        if self.mode == 'ACTIVE_OBJECT':
            active = bpy.context.active_object
            if active:
                objs.append(active)

        elif self.mode == 'SELECTED_OBJECTS':
            for obj in bpy.context.selected_objects:
                objs.append(obj)

        else:
            for obj in bpy.data.objects:
                objs.append(obj)

        return objs

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'objects_folder')

        col = self.layout.column(align=True)
        col.label(text='Mode:')
        col.prop(self, 'mode', expand=True)

    def execute(self, context):
        # search object
        objs = self._get_objs()
        if not objs:
            self.report({'ERROR'}, text.get_text(text.error.no_objs))
            return {'CANCELLED'}

        # get objects and meshes folders
        objs_folder, mshs_folder = self._get_folders()

        prefs_folder = objs_folder
        cur_folder = bpy.path.abspath(self.directory)

        if not cur_folder.startswith(objs_folder):

            if cur_folder.startswith(mshs_folder):
                prefs_folder = mshs_folder
            else:
                self.report(
                    {'ERROR'},
                    text.get_text(text.error.not_inside_objs_mshs_folder)
                )
                self.report({'ERROR'}, cur_folder)
                self.report(
                    {'ERROR'},
                    'Objects Folder: {}'.format(objs_folder)
                )
                self.report(
                    {'ERROR'},
                    'Meshes Folder: {}'.format(mshs_folder)
                )
                return {'CANCELLED'}

        # set export path
        for obj in objs:
            export_path = cur_folder[len(prefs_folder) : ]
            obj.xray.export_path = export_path

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        objs_folder, mshs_folder = self._get_folders()

        if not (objs_folder or mshs_folder):
            self.report(
                {'ERROR'},
                text.get_text(text.error.no_objs_mshs_folder)
            )
            return {'FINISHED'}

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class XRAY_OT_set_asset_author(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.set_asset_author'
    bl_label = 'Set Object Asset Author'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    @utils.set_cursor_state
    def execute(self, context):
        if not context.selected_objects:
            self.report({'ERROR'}, 'No selected objects')
            return {'CANCELLED'}
        changed = 0
        for obj in context.selected_objects:
            asset = obj.asset_data
            if not asset:
                continue
            root = utils.obj.find_root(obj)
            owner = root.xray.revision.owner
            asset.author = owner
            changed += 1
        utils.draw.redraw_areas()
        self.report({'INFO'}, 'Changed Assets: {}'.format(changed))
        return {'FINISHED'}


classes = [
    XRAY_OT_place_objects,
    XRAY_OT_colorize_objects,
    XRAY_OT_set_export_path
]

if utils.version.has_asset_browser():
    classes.append(XRAY_OT_set_asset_author)


def register():
    utils.version.register_classes(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
