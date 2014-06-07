import bpy


class XRayObjectPanel(bpy.types.Panel):
    bl_label = 'XRay'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    def draw_header(self, context):
        self.layout.label(icon='PLUGIN')

    def draw(self, context):
        layout = self.layout
        data = context.object.xray
        layout.prop(data, 'flags')
        layout.prop(data, 'lodref')
        layout.prop(data, 'userdata')


def inject_ui_init():
    bpy.utils.register_class(XRayObjectPanel)


def inject_ui_done():
    bpy.utils.unregister_class(XRayObjectPanel)
