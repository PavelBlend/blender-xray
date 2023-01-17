# standart modules
import os

# blender modules
import bpy

# addon modules
from .. import utils


mode_items = (
    ('REPLACE', 'Replace', ''),
    ('CLEAR', 'Clear', ''),
    ('OBJECT', 'Copy from Object', ''),
    ('ACTIVE', 'Copy from Active Object', ''),
    ('TEXT', 'Copy from Text Data Block', '')
)
change_items = (
    ('ACTIVE', 'Active Object', ''),
    ('SELECTED', 'Selected Objects', ''),
    ('ALL', 'All Objects', '')
)
op_props = {
    'mode': bpy.props.EnumProperty(
        name='Mode',
        items=mode_items,
        default='REPLACE'
    ),
    'change': bpy.props.EnumProperty(
        name='Change',
        items=change_items,
        default='SELECTED'
    ),
    'value': bpy.props.StringProperty(name='Userdata'),
    'obj': bpy.props.StringProperty(name='Object'),
    'text': bpy.props.StringProperty(name='Text')
}


class XRAY_OT_change_userdata(bpy.types.Operator):
    bl_idname = 'io_scene_xray.change_userdata'
    bl_label = 'Change Userdata'
    bl_options = {'REGISTER', 'UNDO'}

    props = op_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))


    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

        column = layout.column(align=True)
        column.label(text='Change:')
        column.prop(self, 'change', expand=True)

        row = utils.version.layout_split(layout, 0.2)

        if self.mode == 'REPLACE':
            row.label(text='Userdata:')
            row.prop(self, 'value', text='')

        elif self.mode == 'OBJECT':
            row.label(text='Object:')
            row.prop_search(self, 'obj', bpy.data, 'objects', text='')

        elif self.mode == 'ACTIVE':
            obj = context.object
            if obj:
                layout.label(text='Active Object: "{}"'.format(obj.name))
            else:
                layout.label(text='No active object!')

        elif self.mode == 'TEXT':
            row.label(text='Text:')
            row.prop_search(self, 'text', bpy.data, 'texts', text='')

    def execute(self, context):
        # search objects
        objects = []
        if self.change == 'ACTIVE':
            if context.object:
                objects.append(context.object)
            else:
                self.report({'INFO'}, 'No active object!')
                return {'FINISHED'}

        elif self.change == 'SELECTED':
            if context.selected_objects:
                for obj in context.selected_objects:
                    objects.append(obj)
            else:
                self.report({'INFO'}, 'No selected objects!')
                return {'FINISHED'}

        elif self.change == 'ALL':
            if bpy.data.objects:
                for obj in bpy.data.objects:
                    objects.append(obj)
            else:
                self.report({'INFO'}, 'Scene has no objects!')
                return {'FINISHED'}

        # search userdata value
        if self.mode == 'REPLACE':
            userdata = self.value

        elif self.mode == 'CLEAR':
            userdata = ''

        elif self.mode == 'OBJECT':
            if self.obj:
                obj = bpy.data.objects.get(self.obj)
                if obj:
                    userdata = obj.xray.userdata
                else:
                    self.report({'INFO'}, 'Cannot find object: "{}"'.format(self.obj))
                    return {'FINISHED'}
            else:
                self.report({'INFO'}, 'Object not specified!')
                return {'FINISHED'}

        elif self.mode == 'ACTIVE':
            obj = context.object
            if obj:
                userdata = obj.xray.userdata
            else:
                self.report({'INFO'}, 'No active object!')
                return {'FINISHED'}

        elif self.mode == 'TEXT':
            if self.text:
                text = bpy.data.texts.get(self.text)
                if text:
                    lines = []
                    for line in text.lines:
                        lines.append(line.body + '\n')
                    userdata = ''.join(lines)
                else:
                    self.report({'INFO'}, 'Cannot find text: "{}"'.format(self.text))
                    return {'FINISHED'}
            else:
                self.report({'INFO'}, 'Text not specified!')
                return {'FINISHED'}

        # search root objects
        root_objs = []
        for obj in objects:
            if obj.xray.isroot:
                root_objs.append(obj)

        if not root_objs:
            self.report({'INFO'}, 'No root-objects!')
            return {'FINISHED'}

        # set value
        for obj in root_objs:
            obj.xray.userdata = userdata

        self.report({'INFO'}, 'Objects Changed: {}'.format(len(root_objs)))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def register():
    utils.version.register_operators(XRAY_OT_change_userdata)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_change_userdata)
