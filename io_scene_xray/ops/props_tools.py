# blender modules
import bpy

# addon modules
from .. import utils


def search_objects(self, context):
    objects = []
    if self.mode == 'ACTIVE':
        if context.active_object:
            objects.append(context.active_object)
        else:
            self.report({'INFO'}, 'No active object!')
            return {'FINISHED'}

    elif self.mode == 'SELECTED':
        if context.selected_objects:
            for obj in context.selected_objects:
                objects.append(obj)
        else:
            self.report({'INFO'}, 'No selected objects!')
            return {'FINISHED'}

    elif self.mode == 'ALL':
        if bpy.data.objects:
            for obj in bpy.data.objects:
                objects.append(obj)
        else:
            self.report({'INFO'}, 'Scene has no objects!')
            return {'FINISHED'}

    # search root objects
    root_objs = []
    for obj in objects:
        if obj.xray.isroot:
            root_objs.append(obj)

    if not root_objs:
        self.report({'INFO'}, 'No root-objects!')
        return {'FINISHED'}

    return root_objs


def join_text_lines(text):
    lines = []
    for line in text.lines:
        lines.append(line.body + '\n')
    value = ''.join(lines)
    return value


def remove_end_line(text):
    lines = []
    for line in text.lines:
        lines.append(line.body)
    value = ' '.join(lines)
    return value


def get_user_data(obj):
    return obj.xray.userdata


def get_motion_refs(obj):
    motion_refs = []
    for ref in obj.xray.motionrefs_collection:
        motion_refs.append(ref.name)
    return '\n'.join(motion_refs)


def get_lod_ref(obj):
    return obj.xray.lodref


def search_value(self, context, prop_name, prop_fun, text_fun):
    if self.value == 'REPLACE':
        value = getattr(self, prop_name)

    elif self.value == 'CLEAR':
        value = ''

    elif self.value == 'OBJECT':
        if self.obj:
            obj = bpy.data.objects.get(self.obj)
            if obj:
                value = prop_fun(obj)
            else:
                self.report(
                    {'INFO'},
                    'Cannot find object: "{}"'.format(self.obj)
                )
                return {'FINISHED'}
        else:
            self.report({'INFO'}, 'Object not specified!')
            return {'FINISHED'}

    elif self.value == 'ACTIVE':
        obj = context.active_object
        if obj:
            value = prop_fun(obj)
        else:
            self.report({'INFO'}, 'No active object!')
            return {'FINISHED'}

    elif self.value == 'TEXT':
        if self.text:
            text = bpy.data.texts.get(self.text)
            if text:
                value = text_fun(text)
            else:
                self.report(
                    {'INFO'},
                    'Cannot find text: "{}"'.format(self.text)
                )
                return {'FINISHED'}
        else:
            self.report({'INFO'}, 'Text not specified!')
            return {'FINISHED'}

    return value


mode_items = (
    ('ACTIVE', 'Active Object', ''),
    ('SELECTED', 'Selected Objects', ''),
    ('ALL', 'All Objects', '')
)


class XRAY_OT_change_userdata(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.change_userdata'
    bl_label = 'Change Userdata'
    bl_options = {'REGISTER', 'UNDO'}

    value = bpy.props.EnumProperty(
        name='Value',
        items=(
            ('REPLACE', 'Replace', 'Set custom value for userdata.'),
            ('CLEAR', 'Clear', 'Remove userdata.'),
            ('OBJECT', 'Object', 'Copy userdata from custom object.'),
            ('ACTIVE', 'Active Object', 'Copy userdata from active object.'),
            ('TEXT', 'Text', 'Copy userdata from text data block.')
        ),
        default='REPLACE'
    )
    mode = bpy.props.EnumProperty(
        name='Mode',
        items=mode_items,
        default='SELECTED'
    )
    userdata = bpy.props.StringProperty(name='Userdata')
    obj = bpy.props.StringProperty(name='Object')
    text = bpy.props.StringProperty(name='Text')

    def draw(self, context):    # pragma: no cover
        layout = self.layout

        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

        column = layout.column(align=True)
        column.label(text='Value:')
        column.prop(self, 'value', expand=True)

        row = utils.version.layout_split(layout, 0.2)

        if self.value == 'REPLACE':
            row.label(text='String:')
            row.prop(self, 'userdata', text='')

        elif self.value == 'OBJECT':
            row.label(text='Object:')
            row.prop_search(self, 'obj', bpy.data, 'objects', text='')

        elif self.value == 'ACTIVE':
            obj = context.active_object
            if obj:
                layout.label(text='Active Object: "{}"'.format(obj.name))
            else:
                layout.label(text='No active object!')

        elif self.value == 'TEXT':
            row.label(text='Text:')
            row.prop_search(self, 'text', bpy.data, 'texts', text='')

    def execute(self, context):
        result = search_objects(self, context)
        if result == {'FINISHED'}:
            return result

        root_objs = result

        result = search_value(
            self,
            context,
            'userdata',
            get_user_data,
            join_text_lines
        )
        if result == {'FINISHED'}:
            return result

        userdata = result

        # set value
        for obj in root_objs:
            obj.xray.userdata = userdata

        utils.draw.redraw_areas()
        self.report({'INFO'}, 'Objects Changed: {}'.format(len(root_objs)))
        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


value_items = (
    ('REPLACE', 'Replace', 'Set custom value for LOD reference.'),
    ('CLEAR', 'Clear', 'Remove LOD reference.'),
    ('OBJECT', 'Object', 'Copy LOD reference from custom object.'),
    ('ACTIVE', 'Active Object', 'Copy LOD reference from active object.'),
    ('TEXT', 'Text', 'Copy LOD reference from text data block.')
)


class XRAY_OT_change_lod_ref(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.change_lod_ref'
    bl_label = 'Change LOD Reference'
    bl_options = {'REGISTER', 'UNDO'}

    value = bpy.props.EnumProperty(
        name='Value',
        items=value_items,
        default='REPLACE'
    )
    mode = bpy.props.EnumProperty(
        name='Mode',
        items=mode_items,
        default='SELECTED'
    )
    lod_ref = bpy.props.StringProperty(name='LOD Reference')
    obj = bpy.props.StringProperty(name='Object')
    text = bpy.props.StringProperty(name='Text')

    def draw(self, context):    # pragma: no cover
        layout = self.layout

        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

        column = layout.column(align=True)
        column.label(text='Value:')
        column.prop(self, 'value', expand=True)

        row = utils.version.layout_split(layout, 0.2)

        if self.value == 'REPLACE':
            row.label(text='String:')
            row.prop(self, 'lod_ref', text='')

        elif self.value == 'OBJECT':
            row.label(text='Object:')
            row.prop_search(self, 'obj', bpy.data, 'objects', text='')

        elif self.value == 'ACTIVE':
            obj = context.active_object
            if obj:
                layout.label(text='Active Object: "{}"'.format(obj.name))
            else:
                layout.label(text='No active object!')

        elif self.value == 'TEXT':
            row.label(text='Text:')
            row.prop_search(self, 'text', bpy.data, 'texts', text='')

    def execute(self, context):
        result = search_objects(self, context)
        if result == {'FINISHED'}:
            return result

        root_objs = result

        result = search_value(
            self,
            context,
            'lod_ref',
            get_lod_ref,
            remove_end_line
        )
        if result == {'FINISHED'}:
            return result

        lod_ref = result

        # set value
        for obj in root_objs:
            obj.xray.lodref = lod_ref

        utils.draw.redraw_areas()
        self.report({'INFO'}, 'Objects Changed: {}'.format(len(root_objs)))
        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


value_items = (
    ('REPLACE', 'Replace', 'Set custom value for motion refs.'),
    ('CLEAR', 'Clear', 'Remove motion refs.'),
    ('OBJECT', 'Object', 'Copy motion refs from custom object.'),
    ('ACTIVE', 'Active Object', 'Copy motion refs from active object.'),
    ('TEXT', 'Text', 'Copy motion refs from text data block.')
)


class XRAY_OT_change_motion_refs(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.change_motion_refs'
    bl_label = 'Change Motion References'
    bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.EnumProperty(
        name='Mode',
        items=(
            ('ADD', 'Add', ''),
            ('OVERWRITE', 'Overwrite', '')
        ),
        default='ADD'
    )
    value = bpy.props.EnumProperty(
        name='Value',
        items=value_items,
        default='REPLACE'
    )
    mode = bpy.props.EnumProperty(
        name='Mode',
        items=mode_items,
        default='SELECTED'
    )
    motion_refs = bpy.props.StringProperty(name='Motion References')
    obj = bpy.props.StringProperty(name='Object')
    text = bpy.props.StringProperty(name='Text')

    def draw(self, context):    # pragma: no cover
        layout = self.layout

        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

        column = layout.column(align=True)
        column.label(text='Value:')
        column.prop(self, 'value', expand=True)

        row = utils.version.layout_split(layout, 0.2)

        if self.value == 'REPLACE':
            row.label(text='String:')
            row.prop(self, 'motion_refs', text='')

        elif self.value == 'OBJECT':
            row.label(text='Object:')
            row.prop_search(self, 'obj', bpy.data, 'objects', text='')

        elif self.value == 'ACTIVE':
            obj = context.active_object
            if obj:
                layout.label(text='Active Object: "{}"'.format(obj.name))
            else:
                layout.label(text='No active object!')

        elif self.value == 'TEXT':
            row.label(text='Text:')
            row.prop_search(self, 'text', bpy.data, 'texts', text='')

    def execute(self, context):
        result = search_objects(self, context)
        if result == {'FINISHED'}:
            return result

        root_objs = result

        result = search_value(
            self,
            context,
            'motion_refs',
            get_motion_refs,
            join_text_lines
        )
        if result == {'FINISHED'}:
            return result

        motion_refs = result

        motion_refs = motion_refs.split('\n')

        # set value
        for obj in root_objs:
            refs = obj.xray.motionrefs_collection
            if self.mode == 'OVERWRITE':
                refs.clear()
            if self.value == 'CLEAR':
                refs.clear()
                continue
            for ref in motion_refs:
                if not ref:
                    continue
                if ref in refs:
                    continue
                elem = refs.add()
                elem.name = ref

        utils.draw.redraw_areas()
        self.report({'INFO'}, 'Objects Changed: {}'.format(len(root_objs)))
        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_change_object_type(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.change_object_type'
    bl_label = 'Change Object Type'
    bl_options = {'REGISTER', 'UNDO'}

    obj_type = bpy.props.EnumProperty(
        name='Type',
        items=(
            ('st', 'Static', ''),
            ('dy', 'Dynamic ', ''),
            ('pd', 'Propgressive Dynamic', ''),
            ('ho', 'HOM', ''),
            ('mu', 'Multiple Usage', ''),
            ('so', 'SOM', ''),
        ),
        default='st'
    )
    mode = bpy.props.EnumProperty(
        name='Mode',
        items=mode_items,
        default='SELECTED'
    )

    def draw(self, context):    # pragma: no cover
        layout = self.layout

        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

        column = layout.column(align=True)
        column.label(text='Type:')
        column.prop(self, 'obj_type', expand=True)

    def execute(self, context):
        result = search_objects(self, context)
        if result == {'FINISHED'}:
            return result

        root_objs = result

        for obj in root_objs:
            obj.xray.flags_simple = self.obj_type

        utils.draw.redraw_areas()
        self.report({'INFO'}, 'Objects Changed: {}'.format(len(root_objs)))
        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_change_hq_export(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.change_hq_export'
    bl_label = 'Change HQ Export'
    bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.EnumProperty(
        name='Mode',
        items=mode_items,
        default='SELECTED'
    )
    hq_export = bpy.props.BoolProperty(name='HQ Export', default=False)

    def draw(self, context):    # pragma: no cover
        layout = self.layout

        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

        layout.prop(self, 'hq_export')

    def execute(self, context):
        result = search_objects(self, context)
        if result == {'FINISHED'}:
            return result

        root_objs = result

        for obj in root_objs:
            obj.xray.flags_custom_hqexp = self.hq_export

        utils.draw.redraw_areas()
        self.report({'INFO'}, 'Objects Changed: {}'.format(len(root_objs)))
        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


classes = (
    XRAY_OT_change_object_type,
    XRAY_OT_change_hq_export,
    XRAY_OT_change_userdata,
    XRAY_OT_change_lod_ref,
    XRAY_OT_change_motion_refs
)


def register():
    for operator in classes:
        utils.version.register_classes(operator)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
