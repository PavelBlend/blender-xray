import bpy


class XRayPanel(bpy.types.Panel):
    bl_label = 'XRay'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw_header(self, context):
        self.layout.label(icon='PLUGIN')


class XRayObjectPanel(XRayPanel):
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        return (
            context.active_object
            and context.active_object.type in {'EMPTY'}
        )

    def draw(self, context):
        layout = self.layout
        data = context.object.xray
        layout.prop(data, 'flags')
        layout.prop(data, 'lodref')
        layout.prop(data, 'userdata')
        layout.prop(data, 'motionrefs')


class XRayMeshPanel(XRayPanel):
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        return (
            context.active_object
            and context.active_object.type in {'MESH'}
        )

    def draw(self, context):
        layout = self.layout
        data = context.object.data.xray
        layout.prop(data, 'flags')
        layout.prop(data, 'options')


class XRayMaterialPanel(XRayPanel):
    bl_context = 'material'

    def draw(self, context):
        layout = self.layout
        data = context.object.active_material.xray
        layout.prop(data, 'flags')
        layout.prop(data, 'eshader')
        layout.prop(data, 'cshader')
        layout.prop(data, 'gamemtl')


class XRayBonePanel(XRayPanel):
    bl_context = 'bone'

    @classmethod
    def poll(cls, context):
        return (
            context.active_object
            and context.active_object.type in {'ARMATURE'}
            and context.active_bone
        )

    def draw(self, context):
        layout = self.layout
        data = context.active_object.data.bones[context.active_bone.name].xray
        layout.prop(data, 'length')
        layout.prop(data, 'gamemtl')
        box = layout.box()
        box.prop(data.shape, 'type', 'shape type')
        box.prop(data.shape, 'flags')
        layout.prop(data, 'ikflags')
        box = layout.box()
        box.prop(data.ikjoint, 'type', 'joint type')
        bx = box.box();
        bx.prop(data.ikjoint, 'lim_x', 'limit X')
        bx.prop(data.ikjoint, 'lim_x_spr', 'spring')
        bx.prop(data.ikjoint, 'lim_x_dmp', 'damping')
        bx = box.box();
        bx.prop(data.ikjoint, 'lim_y', 'limit Y')
        bx.prop(data.ikjoint, 'lim_y_spr', 'spring')
        bx.prop(data.ikjoint, 'lim_y_dmp', 'damping')
        bx = box.box();
        bx.prop(data.ikjoint, 'lim_z', 'limit Z')
        bx.prop(data.ikjoint, 'lim_z_spr', 'spring')
        bx.prop(data.ikjoint, 'lim_z_dmp', 'damping')
        box.prop(data.ikjoint, 'spring')
        box.prop(data.ikjoint, 'damping')
        box = layout.box()
        box.prop(data.breakf, 'force', 'break force')
        box.prop(data.breakf, 'torque', 'break torque')
        layout.prop(data, 'friction')
        box = layout.box()
        box.prop(data.mass, 'value', 'mass')
        box.prop(data.mass, 'center')


classes = [
    XRayObjectPanel
    , XRayMeshPanel
    , XRayMaterialPanel
    , XRayBonePanel
]


def inject_ui_init():
    for c in classes:
        bpy.utils.register_class(c)


def inject_ui_done():
    for c in classes.remove():
        bpy.utils.unregister_class(c)
