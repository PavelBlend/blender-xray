import bpy


class XRayPanel(bpy.types.Panel):
    bl_label = 'XRay'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw_header(self, context):
        self.layout.label(icon='PLUGIN')


class XRayObjectPanel(XRayPanel):
    bl_context = 'object'

    def draw(self, context):
        layout = self.layout
        data = context.object.xray
        layout.prop(data, 'flags')
        layout.prop(data, 'lodref')
        layout.prop(data, 'userdata')


class XRayMaterialPanel(XRayPanel):
    bl_context = 'material'

    def draw(self, context):
        layout = self.layout
        data = context.object.active_material.xray
        layout.prop(data, 'flags')
        layout.prop(data, 'eshader')
        layout.prop(data, 'cshader')
        layout.prop(data, 'gamemtl')


classes = [
    XRayObjectPanel
    , XRayMaterialPanel
]


def inject_ui_init():
    for c in classes:
        bpy.utils.register_class(c)


def inject_ui_done():
    for c in classes.remove():
        bpy.utils.unregister_class(c)
