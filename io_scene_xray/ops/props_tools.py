# blender modules
import bpy

# addon modules
from .. import utils


def search_objects(self, context):
    objects = []

    # active
    if self.mode == 'ACTIVE':
        if context.active_object:
            objects.append(context.active_object)
        else:
            self.report({'ERROR'}, 'No active object!')
            return {'FINISHED'}

    # selected
    elif self.mode == 'SELECTED':
        if context.selected_objects:
            for obj in context.selected_objects:
                objects.append(obj)
        else:
            self.report({'ERROR'}, 'No selected objects!')
            return {'FINISHED'}

    # all
    else:
        if bpy.data.objects:
            for obj in bpy.data.objects:
                objects.append(obj)
        else:
            self.report({'ERROR'}, 'Scene has no objects!')
            return {'FINISHED'}

    # search root objects
    root_objs = []
    for obj in objects:
        if obj.xray.isroot:
            root_objs.append(obj)

    if not root_objs:
        self.report({'ERROR'}, 'No root-objects!')
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


def get_motions(obj):
    motions = []
    for motion in obj.xray.motions_collection:
        motions.append(motion.name)
    return '\n'.join(motions)


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


def _get_mode_prop():
    return bpy.props.EnumProperty(
        name='Mode',
        items=(
            ('ACTIVE', 'Active Object', ''),
            ('SELECTED', 'Selected Objects', ''),
            ('ALL', 'All Objects', '')
        ),
        default='SELECTED'
    )


class _BasePropsOperator(utils.ie.BaseOperator):
    bl_options = {'REGISTER', 'UNDO'}

    def _draw_mode(self):    # pragma: no cover
        layout = self.layout

        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

    def _draw_edit(self):    # pragma: no cover
        layout = self.layout

        column = layout.column(align=True)
        column.label(text='Edit:')
        column.prop(self, 'edit', expand=True)

    def _draw_value(self):    # pragma: no cover
        layout = self.layout

        column = layout.column(align=True)
        column.label(text='Value:')
        column.prop(self, 'value', expand=True)

        row = utils.version.layout_split(layout, 0.2)

        if self.value == 'REPLACE':
            row.label(text='String:')
            row.prop(self, 'string', text='')

        elif self.value == 'OBJECT':
            row.label(text='Object:')
            row.prop_search(self, 'obj', bpy.data, 'objects', text='')

        elif self.value == 'ACTIVE':
            obj = bpy.context.active_object
            if obj:
                layout.label(text='Active Object: "{}"'.format(obj.name))
            else:
                layout.label(text='No active object!')

        elif self.value == 'TEXT':
            row.label(text='Text:')
            row.prop_search(self, 'text', bpy.data, 'texts', text='')

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_change_userdata(_BasePropsOperator):
    bl_idname = 'io_scene_xray.change_userdata'
    bl_label = 'Change Userdata'
    bl_options = {'REGISTER', 'UNDO'}

    mode = _get_mode_prop()
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
    string = bpy.props.StringProperty(name='Userdata')
    obj = bpy.props.StringProperty(name='Object')
    text = bpy.props.StringProperty(name='Text')

    def draw(self, context):    # pragma: no cover
        self._draw_mode()
        self._draw_value()

    def execute(self, context):
        result = search_objects(self, context)
        if result == {'FINISHED'}:
            return result

        root_objs = result

        result = search_value(
            self,
            context,
            'string',
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


value_items = (
    ('REPLACE', 'Replace', 'Set custom value for LOD reference.'),
    ('CLEAR', 'Clear', 'Remove LOD reference.'),
    ('OBJECT', 'Object', 'Copy LOD reference from custom object.'),
    ('ACTIVE', 'Active Object', 'Copy LOD reference from active object.'),
    ('TEXT', 'Text', 'Copy LOD reference from text data block.')
)


class XRAY_OT_change_lod_ref(_BasePropsOperator):
    bl_idname = 'io_scene_xray.change_lod_ref'
    bl_label = 'Change LOD Reference'
    bl_options = {'REGISTER', 'UNDO'}

    mode = _get_mode_prop()
    value = bpy.props.EnumProperty(
        name='Value',
        items=value_items,
        default='REPLACE'
    )
    string = bpy.props.StringProperty(name='LOD Reference')
    obj = bpy.props.StringProperty(name='Object')
    text = bpy.props.StringProperty(name='Text')

    def draw(self, context):    # pragma: no cover
        self._draw_mode()
        self._draw_value()

    def execute(self, context):
        result = search_objects(self, context)
        if result == {'FINISHED'}:
            return result

        root_objs = result

        result = search_value(
            self,
            context,
            'string',
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


value_items = (
    ('REPLACE', 'Replace', 'Set custom value for motion refs.'),
    ('CLEAR', 'Clear', 'Remove motion refs.'),
    ('OBJECT', 'Object', 'Copy motion refs from custom object.'),
    ('ACTIVE', 'Active Object', 'Copy motion refs from active object.'),
    ('TEXT', 'Text', 'Copy motion refs from text data block.')
)


class XRAY_OT_change_motions(_BasePropsOperator):
    bl_idname = 'io_scene_xray.change_motions'
    bl_label = 'Change Motions'
    bl_options = {'REGISTER', 'UNDO'}

    mode = _get_mode_prop()
    edit = bpy.props.EnumProperty(
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
    string = bpy.props.StringProperty(name='Motions')
    obj = bpy.props.StringProperty(name='Object')
    text = bpy.props.StringProperty(name='Text')

    def draw(self, context):    # pragma: no cover
        self._draw_mode()
        self._draw_edit()
        self._draw_value()

    def execute(self, context):
        result = search_objects(self, context)
        if result == {'FINISHED'}:
            return result

        root_objs = result

        result = search_value(
            self,
            context,
            'string',
            get_motions,
            join_text_lines
        )
        if result == {'FINISHED'}:
            return result

        motions = result.split('\n')

        # set value
        for obj in root_objs:
            coll = obj.xray.motions_collection
            if self.edit == 'OVERWRITE':
                coll.clear()
            if self.value == 'CLEAR':
                coll.clear()
                continue
            for motion in motions:
                if not motion:
                    continue
                if motion in coll:
                    continue
                elem = coll.add()
                elem.name = motion

        utils.draw.redraw_areas()
        self.report({'INFO'}, 'Objects Changed: {}'.format(len(root_objs)))
        return {'FINISHED'}


class XRAY_OT_change_motion_refs(_BasePropsOperator):
    bl_idname = 'io_scene_xray.change_motion_refs'
    bl_label = 'Change Motion References'
    bl_options = {'REGISTER', 'UNDO'}

    mode = _get_mode_prop()
    edit = bpy.props.EnumProperty(
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
    string = bpy.props.StringProperty(name='Motion References')
    obj = bpy.props.StringProperty(name='Object')
    text = bpy.props.StringProperty(name='Text')

    def draw(self, context):    # pragma: no cover
        self._draw_mode()
        self._draw_edit()
        self._draw_value()

    def execute(self, context):
        result = search_objects(self, context)
        if result == {'FINISHED'}:
            return result

        root_objs = result

        result = search_value(
            self,
            context,
            'string',
            get_motion_refs,
            join_text_lines
        )
        if result == {'FINISHED'}:
            return result

        motion_refs = result.split('\n')

        # set value
        for obj in root_objs:
            refs = obj.xray.motionrefs_collection
            if self.edit == 'OVERWRITE':
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


class XRAY_OT_change_object_type(_BasePropsOperator):
    bl_idname = 'io_scene_xray.change_object_type'
    bl_label = 'Change Object Type'
    bl_options = {'REGISTER', 'UNDO'}

    mode = _get_mode_prop()
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

    def draw(self, context):    # pragma: no cover
        layout = self.layout

        self._draw_mode()

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


class XRAY_OT_change_hq_export(_BasePropsOperator):
    bl_idname = 'io_scene_xray.change_hq_export'
    bl_label = 'Change HQ Export'
    bl_options = {'REGISTER', 'UNDO'}

    mode = _get_mode_prop()
    hq_export = bpy.props.BoolProperty(name='HQ Export', default=False)

    def draw(self, context):    # pragma: no cover
        layout = self.layout

        self._draw_mode()

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


classes = (
    XRAY_OT_change_object_type,
    XRAY_OT_change_hq_export,
    XRAY_OT_change_userdata,
    XRAY_OT_change_lod_ref,
    XRAY_OT_change_motions,
    XRAY_OT_change_motion_refs
)


def register():
    for operator in classes:
        utils.version.register_classes(operator)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
