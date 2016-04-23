import bpy
from .plugin_prefs import get_preferences
from . import ui_dynmenu
from .utils import create_cached_file_data, parse_shaders, parse_shaders_xrlc, parse_gamemtl


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
        if not data.flags_use_custom:
            layout.prop(data, 'flags_simple', text='Type')
        else:
            row = layout.row(align=True)
            row.prop(data, 'flags_simple', text='Type')
            row.prop(data, 'flags_custom_type', text='')
            col = layout.column(align=True)
            row = col.row(align=True)
            row.prop(data, 'flags_custom_progressive', text='Progressive', toggle=True)
            row.prop(data, 'flags_custom_lod', text='LOD', toggle=True)
            row.prop(data, 'flags_custom_hom', text='HOM', toggle=True)
            row = col.row(align=True)
            row.prop(data, 'flags_custom_musage', text='Multi Usage', toggle=True)
            row.prop(data, 'flags_custom_soccl', text='Sound Occluder', toggle=True)
            row.prop(data, 'flags_custom_hqexp', text='HQ Export', toggle=True)
        layout.prop(data, 'lodref')
        layout.prop(data, 'userdata')
        layout.prop(data, 'motionrefs')

        box = layout.box()
        box.label('Revision:')
        box.prop(data.revision, 'owner', text='Owner')
        box.prop(data.revision, 'ctime_str', text='Created')
        box.prop(data.revision, 'moder', text='Moder')
        box.prop(data.revision, 'mtime_str', text='Modified')


class XRayMeshPanel(XRayPanel):
    bl_context = 'object'
    bl_label = 'XRay - mesh'

    @classmethod
    def poll(cls, context):
        return (
            context.active_object
            and context.active_object.type in {'MESH'}
            and get_preferences().expert_mode
        )

    def draw(self, context):
        layout = self.layout
        data = context.object.data.xray
        r = layout.row(align=True)
        r.prop(data, 'flags_visible', text='Visible', toggle=True)
        r.prop(data, 'flags_locked', text='Locked', toggle=True)
        r.prop(data, 'flags_sgmask', text='SGMask', toggle=True)
        # r.prop(data, 'flags_other', text='Other')


class XRayXrMenuTemplate(ui_dynmenu.DynamicMenu):
    @staticmethod
    def parse(data, fparse):
        def push_dict(d, sp, v):
            if len(sp) == 1:
                d[sp[0]] = v
            else:
                e = d.get(sp[0], None)
                if e is None:
                    d[sp[0]] = e = dict()
                push_dict(e, sp[1:], v)

        def dict_to_array(d):
            result = []
            for (k, v) in d.items():
                if isinstance(v, str):
                    result.append((k, v))
                else:
                    result.append((k, dict_to_array(v)))
            return sorted(result, key=lambda e: e[0])

        tmp = dict()
        for (n, d) in fparse(data):
            sp = n.split('\\')
            push_dict(tmp, sp, n)
        return dict_to_array(tmp)

    @classmethod
    def create_cached(cls, pref_prop, fparse):
        return create_cached_file_data(lambda: getattr(get_preferences(), pref_prop, None), lambda data: cls.parse(data, fparse))

    @classmethod
    def items_for_path(cls, path):
        data = cls.cached()
        if data is None:
            return []
        for p in path:
            data = data[p][1]
        return data


class XRayEShaderMenu(XRayXrMenuTemplate):
    bl_idname = 'io_scene_xray.dynmenu.eshader'
    prop_name = 'eshader'
    cached = XRayXrMenuTemplate.create_cached('eshader_file', parse_shaders)


class XRayCShaderMenu(XRayXrMenuTemplate):
    bl_idname = 'io_scene_xray.dynmenu.cshader'
    prop_name = 'cshader'
    cached = XRayXrMenuTemplate.create_cached('cshader_file', parse_shaders_xrlc)


class XRayGameMtlMenu(XRayXrMenuTemplate):
    bl_idname = 'io_scene_xray.dynmenu.gamemtl'
    prop_name = 'gamemtl'
    cached = XRayXrMenuTemplate.create_cached('gamemtl_file', parse_gamemtl)


def _gen_xr_selector(layout, data, name, text):
    s = layout.row(align=True)
    s.prop(data, name, text=text)
    ui_dynmenu.DynamicMenu.set_layout_context_data(s, data)
    s.menu('io_scene_xray.dynmenu.' + name, icon='TRIA_DOWN')


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


class XRayActionPanel(XRayPanel):
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        return (
            context.active_object and
            context.active_object.animation_data and
            context.active_object.animation_data.action
        )

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        a = obj.animation_data.action
        data = a.xray
        layout.prop(data, 'fps')
        layout.prop(data, 'speed')
        layout.prop(data, 'accrue')
        layout.prop(data, 'falloff')
        layout.prop(data, 'flags_fx', text='Type FX', toggle=True)
        if data.flags_fx:
            row = layout.row(align=True)
            row.label('Start Bone:')
            row.prop_search(data, 'bonestart_name', obj.pose, 'bones', text='')
            layout.prop(data, 'power', text='Power')
        else:
            row = layout.row(align=True)
            row.label('Bone Part:')
            row.prop_search(data, 'bonepart_name', obj.pose, 'bone_groups', text='')
            row = layout.row(align=True)
            row.prop(data, 'flags_stopatend', text='Stop', toggle=True)
            row.prop(data, 'flags_nomix', text='!Mix', toggle=True)
            row.prop(data, 'flags_syncpart', text='Sync', toggle=True)


classes = [
    XRayObjectPanel
    , XRayMeshPanel
    , XRayEShaderMenu
    , XRayCShaderMenu
    , XRayGameMtlMenu
    , XRayMaterialPanel
    , XRayArmaturePanel
    , XRayBonePanel
    , XRayActionPanel
]


def inject_ui_init():
    for c in classes:
        bpy.utils.register_class(c)
    ui_dynmenu.register()


def inject_ui_done():
    ui_dynmenu.unregister()
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
