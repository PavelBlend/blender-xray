# blender modules
import bpy

# addon modules
from .. import utils
from .. import text
from .. import version_utils


mode_items = (
    ('ACTIVE_OBJECT', 'Active Object', ''),
    ('SELECTED_OBJECTS', 'Selected Objects', ''),
    ('ALL_OBJECTS', 'All Objects', '')
)
op_props = {
    'mode': bpy.props.EnumProperty(
        name='Mode',
        default='SELECTED_OBJECTS',
        items=mode_items
    ),
}


class XRAY_OT_verify_uv(bpy.types.Operator):
    bl_idname = 'io_scene_xray.verify_uv'
    bl_label = 'Verify UV'
    bl_description = 'Find UV-maps errors in selected objects'
    bl_options = {'REGISTER', 'UNDO'}

    props = op_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    MINIMUM_VALUE = -32.0
    MAXIMUM_VALUE = 32.0
    BAD_UV = True
    CORRECT_UV = False

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

    @utils.set_cursor_state
    def execute(self, context):
        # set object mode
        if context.object:
            bpy.ops.object.mode_set(mode='OBJECT')
        objects = self.get_objects()
        if not objects:
            bpy.ops.object.select_all(action='DESELECT')
            version_utils.set_active_object(None)
            return {'CANCELLED'}
        bad_objects = []
        for bpy_object in objects:
            uv_status = self.verify_uv(context, bpy_object)
            if uv_status == self.BAD_UV:
                bad_objects.append(bpy_object.name)
        bpy.ops.object.select_all(action='DESELECT')
        for bad_object_name in bad_objects:
            bad_object = bpy.data.objects[bad_object_name]
            version_utils.select_object(bad_object)
        version_utils.set_active_object(None)
        self.report(
            {'INFO'},
            text.get_text(text.warn.incorrect_uv_objs_count).capitalize() + \
            ': {}'.format(len(bad_objects))
        )
        return {'FINISHED'}

    def get_objects(self):
        objects = []
        if self.mode == 'ACTIVE_OBJECT':
            active_obj = bpy.context.object
            if active_obj:
                objects.append(active_obj)
            else:
                self.report(
                    {'WARNING'},
                    text.get_text(text.error.no_active_obj).capitalize()
                )
        elif self.mode == 'SELECTED_OBJECTS':
            if not bpy.context.selected_objects:
                self.report(
                    {'WARNING'},
                    text.get_text(text.error.no_selected_obj).capitalize()
                )
            else:
                objects = [obj for obj in bpy.context.selected_objects]
        elif self.mode == 'ALL_OBJECTS':
            if not bpy.data.objects:
                self.report(
                    {'WARNING'},
                    text.get_text(text.error.no_blend_obj).capitalize()
                )
            else:
                objects = [obj for obj in bpy.context.scene.objects]
        else:
            raise Exception('incorrect verify uv mode')
        return objects

    def verify_uv(self, context, bpy_object):
        if bpy_object.type != 'MESH':
            return self.CORRECT_UV
        version_utils.set_active_object(bpy_object)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        mesh = bpy_object.data
        has_bad_uv = False
        for uv_layer in mesh.uv_layers:
            for polygon in mesh.polygons:
                for loop in polygon.loop_indices:
                    uv = uv_layer.data[loop].uv
                    if not (self.MINIMUM_VALUE < uv.x < self.MAXIMUM_VALUE):
                        polygon.select = True
                        has_bad_uv = True
                    if not (self.MINIMUM_VALUE < uv.y < self.MAXIMUM_VALUE):
                        polygon.select = True
                        has_bad_uv = True
        if has_bad_uv:
            return self.BAD_UV
        else:
            return self.CORRECT_UV

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def register():
    version_utils.register_operators(XRAY_OT_verify_uv)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_verify_uv)
