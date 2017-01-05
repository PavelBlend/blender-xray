import bpy
from .plugin_prefs import get_preferences
from . import ui_dynmenu, ui_list, shape_edit_helper as seh
from .utils import create_cached_file_data, parse_shaders, parse_shaders_xrlc, parse_gamemtl, is_helper_object


class PropClipOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.propclip'
    bl_label = ''

    items = (
        ('copy', '', '', 'COPYDOWN', 0),
        ('paste', '', '', 'PASTEDOWN', 1),
        ('clear', '', '', 'X', 2)
    )
    op = bpy.props.EnumProperty(items=items)
    path = bpy.props.StringProperty()

    def execute(self, context):
        *path, prop = self.path.split('.')
        obj = context
        for pn in path:
            obj = getattr(obj, pn)
        if self.op == 'copy':
            context.window_manager.clipboard = getattr(obj, prop)
        elif self.op == 'paste':
            setattr(obj, prop, context.window_manager.clipboard)
        elif self.op == 'clear':
            setattr(obj, prop, '')
        return {'FINISHED'}

    @classmethod
    def drawall(cls, layout, path, value):
        for i in cls.items:
            l = layout
            if i[0] in ('copy', 'clear') and not value:
                l = l.split(align=True)
                l.enabled = False
            p = l.operator(cls.bl_idname, icon=i[3])
            p.op = i[0]
            p.path = path


class XRayPanel(bpy.types.Panel):
    bl_label = 'XRay'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw_header(self, context):
        self.layout.label(icon='PLUGIN')


class _CollapsOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.collaps'
    bl_label = ''
    bl_description = 'Show / hide UI block'

    key = bpy.props.StringProperty()

    _DATA = {}

    @classmethod
    def get(cls, key):
        return cls._DATA.get(key, False)

    def execute(self, context):
        _CollapsOp._DATA[self.key] = not _CollapsOp.get(self.key)
        return {'FINISHED'}


def draw_collapsible(layout, key, text=None, enabled=None, icon=None, style=None):
    col = layout.column(align=True)
    row = col.row(align=True)
    rw = row
    if (enabled is not None) and (not enabled):
        rw = rw.row(align=True)
        rw.enabled = False
    isshow = _CollapsOp.get(key)
    if icon is None:
        icon = 'TRIA_DOWN' if isshow else 'TRIA_RIGHT'
    kwargs = {}
    if text is not None:
        kwargs['text'] = text
    box = col.box() if isshow else None
    if style == 'tree':
        rw = rw.row()
        rw.alignment = 'LEFT'
        if box:
            bxr = box.row(align=True)
            bxr.alignment = 'LEFT'
            bxr.label('')
            box = bxr.column()
    op = rw.operator(_CollapsOp.bl_idname, icon=icon, emboss=style != 'tree', **kwargs)
    op.key = key
    return row, box


class XRayObjectPanel(XRayPanel):
    bl_context = 'object'
    bl_label = 'XRay - object root'

    @classmethod
    def poll(cls, context):
        return (
            context.active_object
            and not is_helper_object(context.active_object)
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
        layout.prop(data, 'export_path')
        rw, box = draw_collapsible(layout, 'object:userdata', 'User Data', enabled=data.userdata != '', icon='VIEWZOOM')
        PropClipOp.drawall(rw, 'object.xray.userdata', data.userdata)
        if box:
            box = box.column(align=True)
            for line in data.userdata.splitlines():
                box.label(line)
        if data.motionrefs:
            split = layout.split()
            split.alert = True
            split.prop(data, 'motionrefs')
        rw, box = draw_collapsible(layout, 'object:motionsrefs', 'Motion Refs (%d)' % len(data.motionrefs_collection))
        if box:
            row = box.row()
            row.template_list('UI_UL_list', 'name', data, 'motionrefs_collection', data, 'motionrefs_collection_index')
            col = row.column(align=True)
            ui_list.draw_list_ops(col, data, 'motionrefs_collection', 'motionrefs_collection_index')

        box = layout.box()
        box.prop(data.revision, 'owner', text='Owner')
        box.prop(data.revision, 'ctime_str', text='Created')


class XRayMeshPanel(XRayPanel):
    bl_context = 'object'
    bl_label = 'XRay - mesh'

    @classmethod
    def poll(cls, context):
        return (
            context.active_object
            and context.active_object.type in {'MESH'}
            and not is_helper_object(context.active_object)
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


class XRayShapeEditHelperObjectPanel(XRayPanel):
    bl_context = 'object'
    bl_label = 'XRay - shape edit helper'

    @classmethod
    def poll(cls, context):
        return (
            context.active_object
            and seh.is_helper_object(context.active_object)
        )

    def draw(self, context):
        seh.draw_helper(self.layout, context.active_object)


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
        v = data.check_different_version_bones()
        if v != 0:
            from io_scene_xray.xray_inject import XRayBoneProperties
            layout.label('Found bones, edited with ' + XRayBoneProperties.ShapeProperties.fmt_version_different(
                v) + ' version of this plugin', icon='ERROR')
        layout.prop(data, 'display_bone_shapes')


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
        bone = context.active_object.data.bones[context.active_bone.name]
        data = bone.xray
        layout.prop(data, 'length')
        _gen_xr_selector(layout, data, 'gamemtl', 'gamemtl')
        box = layout.box()
        box.prop(data.shape, 'type', 'shape type')
        v = data.shape.check_version_different()
        if v != 0:
            box.label('shape edited with ' + data.shape.fmt_version_different(v) + ' version of this plugin',
                      icon='ERROR')
        seh.draw(box.column(align=True), bone)

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
        from .plugin import OpExportSkl
        layout = self.layout
        obj = context.active_object
        a = obj.animation_data.action
        data = a.xray
        layout.prop(data, 'fps')
        if obj.type != 'ARMATURE':
            return
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
        layout.context_pointer_set(OpExportSkl.bl_idname + '.action', a)
        layout.operator(OpExportSkl.bl_idname, icon='EXPORT')


class XRayScenePanel(XRayPanel):
    bl_context = 'scene'
    bl_label = 'X-Ray Engine Project'

    def draw(self, context):
        from .plugin import OpExportProject

        obj = context.scene
        data = obj.xray

        def gen_op(layout, text, enabled=True, icon='NONE'):
            if not enabled:
                layout = layout.split()
                layout.enabled = False
            props = layout.operator(OpExportProject.bl_idname, text=text, icon=icon)
            return props

        layout = self.layout
        row = layout.row()
        if not data.export_root:
            row.enabled = False
        selection = OpExportProject.find_objects(context, use_selection=True)
        if len(selection) == 0:
            gen_op(row, 'No Roots Selected', enabled=False)
        elif len(selection) == 1:
            gen_op(row, text=selection[0].name + '.object', icon='OUTLINER_OB_MESH').use_selection = True
        else:
            gen_op(row, text='Selected Objects (%d)' % len(selection), icon='GROUP').use_selection = True
        scene = OpExportProject.find_objects(context)
        gen_op(row, text='Scene Export (%d)' % len(scene), icon='SCENE_DATA', enabled=len(scene) != 0).use_selection = False
        l = layout
        if len(data.export_root) == 0:
            l = l.split()
            l.alert = True
        l.prop(data, 'export_root')
        row = layout.split(0.33)
        row.label('Format Version:')
        row.row().prop(data, 'fmt_version', expand=True)
        _, bx = draw_collapsible(layout, 'scene:object', 'Object Export Properties')
        if bx:
            bx.prop(data, 'object_export_motions')
            bx.prop(data, 'object_texture_name_from_image_path')


from .details.ui import XRayDetailsPanel

classes = [
    PropClipOp,
    _CollapsOp,
    XRayObjectPanel
    , XRayMeshPanel
    , XRayDetailsPanel
    , XRayShapeEditHelperObjectPanel
    , XRayEShaderMenu
    , XRayCShaderMenu
    , XRayGameMtlMenu
    , XRayMaterialPanel
    , XRayArmaturePanel
    , XRayBonePanel
    , XRayActionPanel
    , XRayScenePanel
]


def inject_ui_init():
    for c in classes:
        bpy.utils.register_class(c)
    ui_dynmenu.register()
    ui_list.register()
    seh.register()


def inject_ui_done():
    seh.unregister()
    ui_list.unregister()
    ui_dynmenu.unregister()
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
