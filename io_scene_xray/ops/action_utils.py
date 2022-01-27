# blender modules
import bpy

# addon modules
from .. import utils
from .. import xray_ltx
from .. import version_utils


SECTION_NAME = 'action_xray_settings'


def get_xray_settings():
    obj = bpy.context.object
    if not obj:
        return
    anim_data = obj.animation_data
    if anim_data:
        action = anim_data.action
        xray = action.xray
        return xray


def write_buffer_data():
    xray = get_xray_settings()
    buffer_text = ''
    if xray:
        buffer_text += '[{}]\n'.format(SECTION_NAME)
        buffer_text += 'fps = {}\n'.format(xray.fps)
        buffer_text += 'flags = {}\n'.format(xray.flags)
        buffer_text += 'speed = {}\n'.format(xray.speed)
        buffer_text += 'accrue = {}\n'.format(xray.accrue)
        buffer_text += 'falloff = {}\n'.format(xray.falloff)
        buffer_text += 'power = {}\n'.format(xray.power)
        buffer_text += 'bonepart_name = "{}"\n'.format(xray.bonepart_name)
        buffer_text += 'bonestart_name = "{}"\n'.format(xray.bonestart_name)
    bpy.context.window_manager.clipboard = buffer_text


def read_buffer_data():
    xray = get_xray_settings()
    if xray:
        buffer_text = bpy.context.window_manager.clipboard
        ltx = xray_ltx.StalkerLtxParser(None, data=buffer_text)
        section = ltx.sections.get(SECTION_NAME, None)
        if not section:
            return
        params = section.params
        xray.fps = float(params.get('fps'))
        xray.flags = int(params.get('flags'))
        xray.speed = float(params.get('speed'))
        xray.accrue = float(params.get('accrue'))
        xray.falloff = float(params.get('falloff'))
        xray.power = float(params.get('power'))
        xray.bonepart_name = params.get('bonepart_name')
        xray.bonestart_name = params.get('bonestart_name')


class XRAY_OT_copy_action_settings(bpy.types.Operator):
    bl_idname = 'io_scene_xray.copy_action_settings'
    bl_label = 'Copy'

    @utils.set_cursor_state
    def execute(self, context):
        write_buffer_data()
        return {'FINISHED'}


class XRAY_OT_paste_action_settings(bpy.types.Operator):
    bl_idname = 'io_scene_xray.paste_action_settings'
    bl_label = 'Paste'
    bl_options = {'REGISTER', 'UNDO'}

    @utils.set_cursor_state
    def execute(self, context):
        read_buffer_data()
        return {'FINISHED'}


op_props = {
    'change_mode': bpy.props.EnumProperty(
        name='Mode',
        items=(
            ('ACTIVE_ACTION', 'Active Action', ''),
            ('ACTIVE_OBJECT', 'Active Object', ''),
            ('SELECTED_OBJECTS', 'Selected Objects', ''),
            ('ALL_OBJECTS', 'All Objects', ''),
            ('ALL_ACTIONS', 'All Actions', '')
        ),
        default='SELECTED_OBJECTS'
    ),
    'change_auto_bake_mode': bpy.props.BoolProperty(
        name='Change Auto Bake Mode', default=True
    ),
    'auto_bake_mode': bpy.props.EnumProperty(
        name='Auto Bake Mode',
        items=(
            ('auto', 'Auto', ''),
            ('on', 'On', ''),
            ('off', 'Off', '')
        ),
        default='auto'
    ),
    'change_use_custom_thresholds': bpy.props.BoolProperty(
        name='Change Use Custom Thresholds', default=True
    ),
    'use_custom_threshold': bpy.props.BoolProperty(
        name='Use Custom Thresholds', default=True
    ),
    'change_location_threshold': bpy.props.BoolProperty(
        name='Change Location Threshold', default=True
    ),
    'change_rotation_threshold': bpy.props.BoolProperty(
        name='Change Rotation Threshold', default=True
    ),
    'value_location_threshold': bpy.props.FloatProperty(
        name='Location Threshold', default=0.00001, precision=6
    ),
    'value_rotation_threshold': bpy.props.FloatProperty(
        name='Rotation Threshold', default=0.00001, precision=6,
        subtype='ANGLE'
    )
}


class XRAY_OT_change_action_bake_settings(bpy.types.Operator):
    bl_idname = 'io_scene_xray.change_action_bake_settings'
    bl_label = 'Change Action Bake Settings'
    bl_options = {'REGISTER', 'UNDO'}

    props = op_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        layout.label(text='Mode:')
        column = layout.column(align=True)
        column.prop(self, 'change_mode', expand=True)
        # auto bake mode
        layout.prop(self, 'change_auto_bake_mode')
        row = layout.row()
        row.active = self.change_auto_bake_mode
        row.prop(self, 'auto_bake_mode', expand=True)
        # custom thresholds
        layout.prop(self, 'change_use_custom_thresholds')
        row = layout.row()
        row.active = self.change_use_custom_thresholds
        row.prop(self, 'use_custom_threshold', toggle=True)
        # location
        layout.prop(self, 'change_location_threshold')
        row = layout.row()
        row.active = self.change_location_threshold
        row.prop(self, 'value_location_threshold')
        # rotation
        layout.prop(self, 'change_rotation_threshold')
        row = layout.row()
        row.active = self.change_rotation_threshold
        row.prop(self, 'value_rotation_threshold')

    @utils.set_cursor_state
    def execute(self, context):
        actions = set()
        # active action
        if self.change_mode == 'ACTIVE_ACTION':
            obj = context.object
            if obj:
                anim_data = obj.animation_data
                if anim_data:
                    action = anim_data.action
                    if action:
                        actions.add(action)
        # active object
        elif self.change_mode == 'ACTIVE_OBJECT':
            obj = context.object
            if obj:
                for motion in obj.xray.motions_collection:
                    action = bpy.data.actions.get(motion.name)
                    if action:
                        actions.add(action)
        # selected objects
        elif self.change_mode == 'SELECTED_OBJECTS':
            for obj in context.selected_objects:
                for motion in obj.xray.motions_collection:
                    action = bpy.data.actions.get(motion.name)
                    if action:
                        actions.add(action)
        # all objects
        elif self.change_mode == 'ALL_OBJECTS':
            for obj in bpy.data.objects:
                for motion in obj.xray.motions_collection:
                    action = bpy.data.actions.get(motion.name)
                    if action:
                        actions.add(action)
        # all actions
        elif self.change_mode == 'ALL_ACTIONS':
            for action in bpy.data.actions:
                actions.add(action)
        # change settings
        for action in actions:
            xray = action.xray
            # mode
            if self.change_auto_bake_mode:
                xray.autobake = self.auto_bake_mode
            # custom thresholds
            if self.change_use_custom_thresholds:
                xray.autobake_custom_refine = self.use_custom_threshold
            # location
            if self.change_location_threshold:
                xray.autobake_refine_location = self.value_location_threshold
            # rotation
            if self.change_rotation_threshold:
                xray.autobake_refine_rotation = self.value_rotation_threshold
        self.report({'INFO'}, 'Changed {} action(s)'.format(len(actions)))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


part_items = (
    ('NONE', 'None', ''),
    ('OBJECT_NAME', 'Object Name', ''),
    ('MOTION_NAME', 'Motion Name', '')
)
funct_items = (
    ('NONE', 'None', ''),
    ('LOWER', 'Lower', ''),
    ('UPPER', 'Upper', ''),
    ('CAPITALIZE', 'Capitalize', ''),
    ('TITLE', 'Title', '')
)
op_props = {
    'data_mode': bpy.props.EnumProperty(
        name='Data Mode',
        items=(
            ('ACTIVE_MOTION', 'Active Motion', ''),
            ('ACTIVE_OBJECT', 'Active Object', ''),
            ('SELECTED_OBJECTS', 'Selected Objects', ''),
            ('ALL_OBJECTS', 'All Objects', '')
        ),
        default='SELECTED_OBJECTS'
    ),
    # part 1
    'part_1': bpy.props.EnumProperty(
        name='Part',
        items=part_items,
        default='OBJECT_NAME'
    ),
    'prefix_1': bpy.props.StringProperty(name='Prefix', default=''),
    'suffix_1': bpy.props.StringProperty(name='Suffix', default=''),
    'function_1': bpy.props.EnumProperty(
        name='Function',
        items=funct_items,
        default='NONE'
    ),
    'replace_old_1': bpy.props.StringProperty(name='Old', default=''),
    'replace_new_1': bpy.props.StringProperty(name='New', default=''),
    # part 2
    'part_2': bpy.props.EnumProperty(
        name='Part',
        items=part_items,
        default='MOTION_NAME'
    ),
    'prefix_2': bpy.props.StringProperty(name='Prefix', default=''),
    'suffix_2': bpy.props.StringProperty(name='Suffix', default=''),
    'function_2': bpy.props.EnumProperty(
        name='Function',
        items=funct_items,
        default='NONE'
    ),
    'replace_old_2': bpy.props.StringProperty(name='Old', default=''),
    'replace_new_2': bpy.props.StringProperty(name='New', default='')
}


class XRAY_OT_rename_actions(bpy.types.Operator):
    bl_idname = 'io_scene_xray.rename_actions'
    bl_label = 'Rename Actions'
    bl_options = {'REGISTER', 'UNDO'}

    props = op_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        column = self.layout.column(align=True)

        column.label(text='Data Mode:')
        column.prop(self, 'data_mode', expand=True)

        part_1 = self.calc_name('object_name', 'motion_name', 0)
        part_2 = self.calc_name('object_name', 'motion_name', 1)
        example = '{0}{1}{2}{3}{4}{5}'.format(
            # part 1
            self.prefix_1,
            part_1,
            self.suffix_1,
            # part 2
            self.prefix_2,
            part_2,
            self.suffix_2
        )
        column.label(text='Result:')
        column.label(text=example)

        for index in (1, 2):
            box = column.box()
            box.label(text='Part {}:'.format(index))
            box.prop(self, 'prefix_{}'.format(index))
            box.row().prop(self, 'part_{}'.format(index), expand=True)
            box.prop(self, 'suffix_{}'.format(index))
            box.label(text='Replace:')
            row = box.row()
            row.label(text='Old:')
            row.prop(self, 'replace_old_{}'.format(index), text='')
            row.label(text='New:')
            row.prop(self, 'replace_new_{}'.format(index), text='')
            row = box.row()
            row.prop(self, 'function_{}'.format(index), expand=True)

    def add_motion(self, obj, index):
        motion = obj.xray.motions_collection[index]
        action = bpy.data.actions.get(motion.name)
        if action:
            if obj.xray.use_custom_motion_names:
                if motion.export_name:
                    export_name = motion.export_name
                else:
                    export_name = action.name
            else:
                export_name = action.name
            self.motions.add((obj, action, export_name, index))

    def add_object_motions(self, obj):
        for motion_index in range(len(obj.xray.motions_collection)):
            self.add_motion(obj, motion_index)

    def calc_name(self, obj_name, export_name, index):
        # base name
        parts = (self.part_1, self.part_2)
        if parts[index] == 'OBJECT_NAME':
            result = obj_name
        elif parts[index] == 'MOTION_NAME':
            result = export_name
        else:
            result = ''

        # replace
        replace_old = (self.replace_old_1, self.replace_old_2)[index]
        replace_new = (self.replace_new_1, self.replace_new_2)[index]
        result = result.replace(replace_old, replace_new)

        # function 1
        functs = (self.function_1, self.function_2)
        if functs[index] == 'LOWER':
            result = result.lower()
        elif functs[index] == 'UPPER':
            result = result.upper()
        elif functs[index] == 'CAPITALIZE':
            result = result.capitalize()
        elif functs[index] == 'TITLE':
            result = result.title()
        else:
            result = result

        return result

    @utils.set_cursor_state
    def execute(self, context):
        obj = context.object
        if not obj and self.data_mode in ('ACTIVE_MOTION', 'ACTIVE_OBJECT'):
            self.report({'WARNING'}, 'No active object!')
            return {'FINISHED'}
        self.motions = set()
        if self.data_mode == 'ACTIVE_MOTION':
            self.add_motion(obj, obj.xray.motions_collection_index)
        elif self.data_mode == 'ACTIVE_OBJECT':
            self.add_object_motions(obj)
        elif self.data_mode == 'SELECTED_OBJECTS':
            for obj in context.selected_objects:
                self.add_object_motions(obj)
        else:
            for obj in bpy.data.objects:
                self.add_object_motions(obj)
        renamed = 0
        not_renamed = 0
        custom_name_objs = set()
        no_custom_name_objs = set()
        for obj, action, export_name, index in self.motions:
            part_1 = self.calc_name(obj.name, export_name, 0)
            part_2 = self.calc_name(obj.name, export_name, 1)
            # rename
            result_name = '{0}{1}{2}{3}{4}{5}'.format(
                # part 1
                self.prefix_1,
                part_1,
                self.suffix_1,
                # part 2
                self.prefix_2,
                part_2,
                self.suffix_2
            )
            if len(result_name) > 63:
                not_renamed += 1
                continue
            motion = obj.xray.motions_collection[index]
            if not motion.export_name:
                motion.export_name = motion.name
            action.name = result_name
            motion.name = action.name
            if motion.name == motion.export_name:
                motion.export_name = ''
                no_custom_name_objs.add(obj)
            else:
                custom_name_objs.add(obj)
            renamed += 1
        for obj in custom_name_objs:
            obj.xray.use_custom_motion_names = True
        no_custom_name_objs = no_custom_name_objs - custom_name_objs
        for obj in no_custom_name_objs:
            obj.xray.use_custom_motion_names = False
        self.report(
            {'INFO'},
            'Renamed: {}, Not Renamed: {}'.format(renamed, not_renamed)
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


classes = (
    XRAY_OT_copy_action_settings,
    XRAY_OT_paste_action_settings,
    XRAY_OT_change_action_bake_settings,
    XRAY_OT_rename_actions
)


def register():
    version_utils.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
