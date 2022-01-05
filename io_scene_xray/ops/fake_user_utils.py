# blender modules
import bpy

# addon modules
from .. import version_utils


mode_items = (
    ('ACTIVE_OBJECT', 'Active Object', ''),
    ('SELECTED_OBJECTS', 'Selected Objects', ''),
    ('ALL_OBJECTS', 'All Objects', ''),
    ('ALL_DATA', 'All Data', '')
)
data_items = (
    ('OBJECTS', 'Objects', ''),
    ('MESHES', 'Meshes', ''),
    ('MATERIALS', 'Materials', ''),
    ('TEXTURES', 'Textures', ''),
    ('IMAGES', 'Images', ''),
    ('ARMATURES', 'Armatures', ''),
    ('ACTIONS', 'Actions', ''),
    ('ALL', 'All', '')
)
fake_items = (
    ('TRUE', 'True', ''),
    ('FALSE', 'False', ''),
    ('INVERT', 'Invert', '')
)
props = {
    'mode': bpy.props.EnumProperty(
        default='SELECTED_OBJECTS',
        items=mode_items
    ),
    'data': bpy.props.EnumProperty(
        default={'ALL'},
        items=data_items,
        options={'ENUM_FLAG'}
    ),
    'fake_user': bpy.props.EnumProperty(
        default='TRUE',
        items=fake_items
    )
}


class XRAY_OT_change_fake_user(bpy.types.Operator):
    bl_idname = 'io_scene_xray.change_fake_user'
    bl_label = 'Change Fake User'
    bl_options = {'REGISTER', 'UNDO'}

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)
        column.label(text='Change:')
        column.prop(self, 'data', expand=True)
        column.label(text='Fake User:')
        column.row().prop(self, 'fake_user', expand=True)

    def execute(self, context):
        print(1)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def register():
    version_utils.assign_props(
        [(props, XRAY_OT_change_fake_user), ]
    )
    bpy.utils.register_class(XRAY_OT_change_fake_user)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_change_fake_user)
