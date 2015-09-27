import bpy


class XRayPanel(bpy.types.Panel):
    bl_label = 'XRay'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw_header(self, context):
        self.layout.label(icon='PLUGIN')


class XRayObjectPanel(XRayPanel):
    bl_context = 'object'
    bl_label = 'XRay - object root'

    @classmethod
    def poll(cls, context):
        return (
            context.active_object
        )

    def draw_header(self, context):
        self.layout.prop(context.object.xray, 'isroot', text='')

    def draw(self, context):
        layout = self.layout
        data = context.object.xray
        layout.enabled = data.isroot
        layout.prop(data, 'flags_simple', text='Type')
        if data.flags_simple_other:
            layout.prop(data, 'flags', text='Type Flags')
        layout.prop(data, 'lodref')
        layout.prop(data, 'userdata')
        layout.prop(data, 'motionrefs')


class XRayMeshPanel(XRayPanel):
    bl_context = 'object'
    bl_label = 'XRay - mesh'

    @classmethod
    def poll(cls, context):
        return (
            context.active_object
            and context.active_object.type in {'MESH'}
        )

    def draw(self, context):
        layout = self.layout
        data = context.object.data.xray
        r = layout.row(align=True)
        r.prop(data, 'flags_visible', text='Visible', toggle=True)
        r.prop(data, 'flags_locked', text='Locked', toggle=True)
        r.prop(data, 'flags_sgmask', text='SGMask', toggle=True)
        # r.prop(data, 'flags_other', text='Other')


def _gen_xr_selector(layout, data, name, text):
    is_custom = getattr(data, name + '_enum') == 'Custom'
    if is_custom:
        layout = layout.row(align=True)
    layout.prop(data, name + '_enum', text=text)
    if is_custom:
        layout.prop(data, name, text='')


class XRayMaterialPanel(XRayPanel):
    bl_context = 'material'

    @classmethod
    def poll(cls, context):
        return context.object.active_material

    def draw(self, context):
        layout = self.layout
        data = context.object.active_material.xray
        layout.prop(data, 'flags_twosided', 'Two sided', toggle=True)
        _gen_xr_selector(layout, data, 'eshader', 'EShader')
        _gen_xr_selector(layout, data, 'cshader', 'CShader')
        _gen_xr_selector(layout, data, 'gamemtl', 'GameMtl')


class XRayArmaturePanel(XRayPanel):
    bl_context = 'data'

    @classmethod
    def poll(cls, context):
        return (
            context.active_object
            and context.active_object.type == 'ARMATURE'
        )

    def draw(self, context):
        layout = self.layout
        data = context.active_object.data.xray
        layout.prop(data, 'display_bone_shapes')
        if data.version < 4:
            layout.label('This armature was imported with obsolete version of this plugin', icon='ERROR')


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
        _gen_xr_selector(layout, data, 'gamemtl', 'gamemtl')
        box = layout.box()
        box.prop(data.shape, 'type', 'shape type')
        row = box.row(align=True)
        row.prop(data.shape, 'flags_nopickable', text='No pickable', toggle=True)
        row.prop(data.shape, 'flags_nophysics', text='No physics', toggle=True)
        row.prop(data.shape, 'flags_removeafterbreak', text='Remove after break', toggle=True)
        row.prop(data.shape, 'flags_nofogcollider', text='No fog collider', toggle=True)
        box = layout.box()
        box.prop(data.ikjoint, 'type', 'joint type')
        if int(data.ikjoint.type):
            box.prop(data, 'friction')
        bx = box.box();
        bx.label('limit x')
        bx.prop(data.ikjoint, 'lim_x_spr', 'spring')
        bx.prop(data.ikjoint, 'lim_x_dmp', 'damping')
        bx = box.box();
        bx.label('limit y')
        bx.prop(data.ikjoint, 'lim_y_spr', 'spring')
        bx.prop(data.ikjoint, 'lim_y_dmp', 'damping')
        bx = box.box();
        bx.label('limit z')
        bx.prop(data.ikjoint, 'lim_z_spr', 'spring')
        bx.prop(data.ikjoint, 'lim_z_dmp', 'damping')
        box.prop(data.ikjoint, 'spring')
        box.prop(data.ikjoint, 'damping')
        if data.ikflags_breakable:
            box = layout.box()
            box.prop(data, 'ikflags_breakable', 'Breakable', toggle=True)
            box.prop(data.breakf, 'force', 'break force')
            box.prop(data.breakf, 'torque', 'break torque')
        else:
            layout.prop(data, 'ikflags_breakable', 'Breakable', toggle=True)
        box = layout.box()
        box.prop(data.mass, 'value', 'mass')
        box.prop(data.mass, 'center')


classes = [
    XRayObjectPanel
    , XRayMeshPanel
    , XRayMaterialPanel
    , XRayArmaturePanel
    , XRayBonePanel
]


def inject_ui_init():
    for c in classes:
        bpy.utils.register_class(c)


def inject_ui_done():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
