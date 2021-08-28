# blender modules
import bpy

# addon modules
from .. import version_utils


place_objects_props = {
    'rows': bpy.props.IntProperty(name='Rows', default=1, min=1, max=1000),
    'offset_x': bpy.props.FloatProperty(
        name='Horizontal Offset', default=2.0, min=0.001
    ),
    'offset_z': bpy.props.FloatProperty(
        name='Vertical Offset', default=2.0, min=0.001
    )
}


class XRAY_OT_place_objects(bpy.types.Operator):
    bl_idname = 'io_scene_xray.place_objects'
    bl_label = 'Place Selected Objects'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    if not version_utils.IS_28:
        for prop_name, prop_value in place_objects_props.items():
            exec('{0} = place_objects_props.get("{0}")'.format(prop_name))

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        column.prop(self, 'rows')
        column.prop(self, 'offset_x')
        column.prop(self, 'offset_z')

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
            obj.location.x = column * self.offset_x
            obj.location.y = 0.0
            obj.location.z = row * self.offset_z
            if ((column + offset) % objects_in_row) == 0 and column != 0:
                column = 0
                row += 1
            else:
                column += 1
        self.report({'INFO'}, 'Moved {0} objects'.format(objects_count))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


classes = (
    (XRAY_OT_place_objects, place_objects_props),
)


def register():
    for operator, props in classes:
        if props:
            version_utils.assign_props([(props, operator), ])
        bpy.utils.register_class(operator)


def unregister():
    for operator, props in reversed(classes):
        bpy.utils.unregister_class(operator)
