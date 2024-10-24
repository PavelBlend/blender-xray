# blender modules
import bpy

# addon modules
from .. import ui
from .. import utils
from .. import ops
from .. import text
from .. import formats


items = (
    ('copy', '', '', 'COPYDOWN', 0),
    ('paste', '', '', 'PASTEDOWN', 1),
    ('clear', '', '', 'X', 2)
)


class XRAY_OT_prop_clip(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.propclip'
    bl_label = ''

    oper = bpy.props.EnumProperty(items=items)
    path = bpy.props.StringProperty()

    def execute(self, context):
        *path, prop = self.path.split('.')
        obj = context

        for name in path:
            obj = getattr(obj, name)

        if self.oper == 'copy':
            context.window_manager.clipboard = getattr(obj, prop)

        elif self.oper == 'paste':
            setattr(obj, prop, context.window_manager.clipboard)

        elif self.oper == 'clear':
            setattr(obj, prop, '')

        return {'FINISHED'}

    @classmethod
    def drawall(cls, layout, path, value):
        for item in items:
            row = layout.row(align=True)

            if item[0] in ('copy', 'clear') and not value:
                row.enabled = False

            props = row.operator(cls.bl_idname, icon=item[3])
            props.oper = item[0]
            props.path = path


def draw_motion_list_elements(layout):
    layout.operator(
        ui.motion_list.XRAY_OT_add_all_actions.bl_idname,
        text='',
        icon='ACTION'
    )
    layout.operator(
        ui.motion_list.XRAY_OT_clean_actions.bl_idname,
        text='',
        icon='BRUSH_DATA'
    )
    layout.operator(
        ui.motion_list.XRAY_OT_remove_all_actions.bl_idname,
        text='',
        icon='X'
    )
    layout.operator(
        ui.motion_list.XRAY_OT_copy_actions.bl_idname,
        text='',
        icon='COPYDOWN'
    )
    layout.operator(
        ui.motion_list.XRAY_OT_paste_actions.bl_idname,
        text='',
        icon='PASTEDOWN'
    )
    layout.operator(
        ui.motion_list.XRAY_OT_sort_actions.bl_idname,
        text='',
        icon='SORTALPHA'
    )


def draw_motion_refs_elements(layout):
    layout.operator(
        ui.motion_refs.XRAY_OT_remove_all_motion_refs.bl_idname,
        text='',
        icon='X'
    )
    layout.operator(
        ui.motion_refs.XRAY_OT_copy_motion_refs_list.bl_idname,
        text='',
        icon='COPYDOWN'
    )
    layout.operator(
        ui.motion_refs.XRAY_OT_paste_motion_refs_list.bl_idname,
        text='',
        icon='PASTEDOWN'
    )
    layout.operator(
        ui.motion_refs.XRAY_OT_sort_motion_refs_list.bl_idname,
        text='',
        icon='SORTALPHA'
    )
    layout.operator(
        ui.motion_refs.XRAY_OT_add_motion_ref_from_file.bl_idname,
        text='',
        icon='FILE_FOLDER'
    )


def draw_object_props(layout, data):
    object_box = layout.box()

    # object type
    split = utils.version.layout_split(object_box, 0.333)
    split.label(text=text.get_iface(text.iface.obj_type) + ':')
    split.prop(data, 'flags_simple', text='')

    if data.flags_use_custom:

        # static/dynamic
        row = object_box.row(align=True)
        row.prop(data, 'flags_custom_type', expand=True)

        # flags
        col = object_box.column(align=True)

        row = col.row(align=True)

        row.prop(
            data,
            'flags_custom_progressive',
            text='Progressive',
            toggle=True
        )
        row.prop(data, 'flags_custom_lod', text='LOD', toggle=True)
        row.prop(data, 'flags_custom_hom', text='HOM', toggle=True)

        row = col.row(align=True)

        row.prop(
            data,
            'flags_custom_musage',
            text='Multiple Usage',
            toggle=True
        )
        row.prop(
            data,
            'flags_custom_soccl',
            text='Sound Occluder',
            toggle=True
        )

    # high quality export
    object_box.prop(
        data,
        'flags_custom_hqexp',
        text=text.get_iface(text.iface.hq_export)
    )

    # lod reference
    split = utils.version.layout_split(object_box, 0.333)
    split.label(text=text.get_iface(text.iface.lod_ref) + ':')
    split.prop(data, 'lodref', text='')

    # export path
    split = utils.version.layout_split(object_box, 0.333)
    split.label(text=text.get_iface(text.iface.exp_path) + ':')
    row = split.row(align=True)

    row.prop(data, 'export_path', text='')

    row.operator(
        ops.obj.XRAY_OT_set_export_path.bl_idname,
        text='',
        icon='FILE_FOLDER'
    )

    # user data
    row, box = ui.collapsible.draw(
        object_box,
        'object:userdata',
        text.get_iface(text.iface.user_data),
        enabled=data.userdata != '',
        icon='VIEWZOOM'
    )
    XRAY_OT_prop_clip.drawall(row, 'object.xray.userdata', data.userdata)

    if box:

        if data.userdata:
            box = box.column(align=True)
            for line in data.userdata.splitlines():
                box.label(text=line)

        else:
            ui.collapsible.XRAY_OT_collaps.set_value('object:userdata', False)

    # motions list
    if data.motions:
        split = object_box.split()
        split.alert = True
        split.prop(data, 'motions')

    _, box = ui.collapsible.draw(
        object_box,
        'object:motions',
        '{} ({})'.format(
            text.get_iface(text.iface.motions),
            len(data.motions_collection)
        )
    )

    if box:
        col = box.column(align=True)

        # play active motion
        col.prop(
            data,
            'play_active_motion',
            text=text.get_iface(text.iface.play_active_motion),
            toggle=True,
            icon='PLAY'
        )

        # use custom names
        col.prop(
            data,
            'use_custom_motion_names',
            text=text.get_iface(text.iface.custom_names),
            toggle=True,
            icon='SORTALPHA'
        )

        # show motion names
        names_row = col.row()
        names_row.label(text=text.get_iface(text.iface.show) + ':')
        names_row.prop(data, 'show_motions_names', expand=True)

        # dependency object
        split = utils.version.layout_split(col, 0.333)
        split.label(text='Dependency' + ':')
        split.prop_search(
            data,
            'dependency_object',
            bpy.data,
            'objects',
            text=''
        )

        # motions
        row = box.row()
        row.template_list(
            ui.motion_list.XRAY_UL_motion_list.bl_idname,
            'name',
            data,
            'motions_collection',
            data,
            'motions_collection_index',
            rows=9
        )

        # motion list operators
        col = row.column(align=True)
        ui.list_helper.draw_list_ops(
            col,
            data,
            'motions_collection',
            'motions_collection_index',
            custom_elements_func=draw_motion_list_elements
        )

    # motion references
    if data.motionrefs:
        split = object_box.split()
        split.alert = True
        split.prop(data, 'motionrefs')

    _, box = ui.collapsible.draw(
        object_box,
        'object:motionsrefs',
        '{} ({})'.format(
            text.get_iface(text.iface.motion_refs),
            len(data.motionrefs_collection)
        )
    )

    if box:

        # load active motion reference
        box.prop(
            data,
            'load_active_motion_refs',
            text=text.get_iface(text.iface.load_motion_ref),
            toggle=True
        )

        if data.load_active_motion_refs:
            row = box.row()
            row.label(text=text.get_iface(text.iface.fmt) + ':')
            row.prop(data.motions_browser, 'file_format', expand=True)

        # motion references
        row = box.row()
        row.template_list(
            'UI_UL_list',
            'name',
            data,
            'motionrefs_collection',
            data,
            'motionrefs_collection_index',
            rows=8
        )

        # motion reference operators
        col = row.column(align=True)
        ui.list_helper.draw_list_ops(
            col,
            data,
            'motionrefs_collection',
            'motionrefs_collection_index',
            custom_elements_func=draw_motion_refs_elements
        )

    # revision
    _, box = ui.collapsible.draw(
        object_box,
        'object:revision',
        text.get_iface(text.iface.revision)
    )

    if box:

        # owner
        split = utils.version.layout_split(box, 0.35)
        split.label(text=text.get_iface(text.iface.owner_name) + ':')
        split.prop(data.revision, 'owner', text='')

        # created time
        split = utils.version.layout_split(box, 0.35)
        split.label(text=text.get_iface(text.iface.created_time) + ':')
        split.prop(data.revision, 'ctime_str', text='')

        # modif name
        split = utils.version.layout_split(box, 0.35)
        split.label(text=text.get_iface(text.iface.moder_name) + ':')
        split.label(text=data.revision.moder)

        # modified time
        split = utils.version.layout_split(box, 0.35)
        split.label(text=text.get_iface(text.iface.mod_time) + ':')
        split.label(text=data.revision.mtime_str)

        # time formats
        subbox = box.box()
        split = utils.version.layout_split(subbox, 0.25)
        split.label(text='')
        split.label(text=text.get_iface(text.iface.time_fmt) + ':', icon='INFO')
        subbox.label(text=text.get_iface(text.iface.time_fmt_1))
        subbox.label(text=text.get_iface(text.iface.time_fmt_2))


def draw_details_props(layout, context):
    box = layout.box()

    if not (context.active_object.type in {'MESH', 'EMPTY'}):
        box.label(
            text='Active object is not a mesh or empty',
            icon='ERROR'
        )
        return

    if context.active_object.type == 'MESH':

        model = context.active_object.xray.detail.model

        col = box.column(align=True)
        col.label(text=text.get_iface(text.iface.dm_props) + ':')

        col.prop(model, 'no_waving', text=text.get_iface(text.iface.dm_no_waving), toggle=True)
        col.prop(model, 'min_scale', text=text.get_iface(text.iface.dm_min_scale))
        col.prop(model, 'max_scale', text=text.get_iface(text.iface.dm_max_scale))
        col.prop(model, 'index', text=text.get_iface(text.iface.dm_index))
        col.prop(model, 'color', text='')

    elif context.active_object.type == 'EMPTY':

        slots = context.active_object.xray.detail.slots

        box.label(text=text.get_iface(text.iface.details_props) + ':')

        split = utils.version.layout_split(box, 0.4, align=True)
        split.label(text=text.get_iface(text.iface.details_meshes) + ':')
        split.prop_search(
            slots,
            'meshes_object',
            bpy.data,
            'objects',
            text=''
        )

        split = utils.version.layout_split(box, 0.4, align=True)
        split.label(text=text.get_iface(text.iface.details_slots_base) + ':')
        split.prop_search(
            slots,
            'slots_base_object',
            bpy.data,
            'objects',
            text=''
        )

        split = utils.version.layout_split(box, 0.4, align=True)
        split.label(text=text.get_iface(text.iface.details_slots_top) + ':')
        split.prop_search(
            slots,
            'slots_top_object',
            bpy.data,
            'objects',
            text=''
        )

        _, box_ = ui.collapsible.draw(
            box,
            'object:lighting',
            text.get_iface(text.iface.details_light_coefs)
        )

        if box_:

            ligthing = slots.ligthing
            box_.label(text=text.get_iface(text.iface.fmt) + ':')
            row = box_.row()
            row.prop(ligthing, 'format', expand=True, text='Format')

            box_.prop_search(
                ligthing,
                'lights_image',
                bpy.data,
                'images',
                text='Lights'
            )

            if ligthing.format == 'builds_1569-cop':

                box_.prop_search(
                    ligthing,
                    'hemi_image',
                    bpy.data,
                    'images',
                    text='Hemi'
                )

                box_.prop_search(
                    ligthing,
                    'shadows_image',
                    bpy.data,
                    'images',
                    text='Shadows'
                )

        _, box_ = ui.collapsible.draw(
            box,
            'object:slots',
            text.get_iface(text.iface.details_meshes_indices)
        )

        if box_:
            for mesh_index in range(4):
                box_.prop_search(
                    slots.meshes,
                    'mesh_{}'.format(mesh_index),
                    bpy.data,
                    'images',
                    text='{0} {1}'.format(
                        text.get_iface(text.iface.details_mesh),
                        mesh_index
                    )
                )

        box.operator(
            formats.details.ops.XRAY_OT_pack_details_images.bl_idname,
            text=text.get_iface(text.iface.details_pack)
        )


def draw_split_prop(layout, owner, prop, label):
    split = utils.version.layout_split(layout, 0.333, align=True)
    split.label(text=label+':')
    split.prop(owner, prop, text='')


def draw_split_prop_search(layout, owner, prop, label, search_owner, search_prop):
    split = utils.version.layout_split(layout, 0.333, align=True)
    split.label(text=label+':')
    split.prop_search(owner, prop, search_owner, search_prop, text='')


def draw_level_props(layout, data):
    box = layout.box()
    level = data.level
    draw_split_prop(box, level, 'object_type', 'Type')
    object_type = level.object_type

    if object_type == 'LEVEL':
        draw_split_prop_search(
            box,
            level,
            'sectors_obj',
            'Sectors Object',
            bpy.data,
            'objects'
        )
        draw_split_prop_search(
            box,
            level,
            'portals_obj',
            'Portals Object',
            bpy.data,
            'objects'
        )
        draw_split_prop_search(
            box,
            level,
            'lights_obj',
            'Lights Object',
            bpy.data,
            'objects'
        )
        draw_split_prop_search(
            box,
            level,
            'glows_obj',
            'Glows Object',
            bpy.data,
            'objects'
        )

    elif object_type == 'PORTAL':
        for portal in ('front', 'back'):
            prop_name = 'sector_' + portal
            draw_split_prop_search(
                box,
                level,
                prop_name,
                prop_name.replace('_', ' ').title(),
                bpy.data,
                'objects'
            )

    elif object_type == 'VISUAL':
        draw_split_prop(box, level, 'visual_type', 'Visual Type')

        if level.visual_type in {'TREE_ST', 'TREE_PM'}:
            # color scale
            color_scale_box = box.box()
            color_scale_box.label(text='Color Scale:')

            col = color_scale_box.row()
            col.prop(level, 'color_scale_rgb')

            col = color_scale_box.row()
            col.prop(level, 'color_scale_hemi')

            col = color_scale_box.row()
            col.prop(level, 'color_scale_sun')

            # color bias
            color_bias_box = box.box()
            color_bias_box.label(text='Color Bias:')

            col = color_bias_box.row()
            col.prop(level, 'color_bias_rgb')

            col = color_bias_box.row()
            col.prop(level, 'color_bias_hemi')

            col = color_bias_box.row()
            col.prop(level, 'color_bias_sun')

        elif level.visual_type in {'NORMAL', 'PROGRESSIVE'}:
            box.prop(level, 'use_fastpath')

    elif object_type == 'LIGHT_DYNAMIC':
        draw_split_prop(box, level, 'controller_name', 'Controller')
        draw_split_prop(box, level, 'light_type_name', 'Light Type')

        row = box.row()
        row.prop(level, 'diffuse')

        row = box.row()
        row.prop(level, 'specular')

        row = box.row()
        row.prop(level, 'ambient')

        box.prop(level, 'range_')
        box.prop(level, 'falloff')
        box.prop(level, 'attenuation_0')
        box.prop(level, 'attenuation_1')
        box.prop(level, 'attenuation_2')
        box.prop(level, 'theta')
        box.prop(level, 'phi')


def get_used(prefs):
    object_used = (
        # import plugins
        prefs.enable_object_import or
        prefs.enable_skls_import or
        prefs.enable_scene_import or
        prefs.enable_omf_import or
        prefs.enable_ogf_import or
        prefs.enable_part_import or
        prefs.enable_group_import or
        # export plugins
        prefs.enable_object_export or
        prefs.enable_skls_export or
        prefs.enable_skl_export or
        prefs.enable_scene_export or
        prefs.enable_part_export or
        prefs.enable_omf_export or
        prefs.enable_ogf_export or
        prefs.enable_group_export
    )
    details_used = (
        # import plugins
        prefs.enable_dm_import or
        prefs.enable_details_import or
        # export plugins
        prefs.enable_dm_export or
        prefs.enable_details_export
    )
    game_level_used = (
        # import plugins
        prefs.enable_level_import or
        # export plugins
        prefs.enable_level_export
    )
    return object_used, details_used, game_level_used


class XRAY_PT_object(ui.base.XRayPanel):
    bl_context = 'object'
    bl_label = ui.base.build_label('Object')

    @classmethod
    def poll(cls, context):
        bpy_obj = context.active_object

        if not bpy_obj:
            return False

        is_helper = utils.obj.is_helper_object(bpy_obj)

        if is_helper:
            return False

        pref = utils.version.get_preferences()
        object_used, details_used, game_level_used = get_used(pref)

        return object_used or details_used or game_level_used

    def draw(self, context):
        pref = utils.version.get_preferences()
        object_used, details_used, game_level_used = get_used(pref)

        layout = self.layout
        obj = context.active_object
        data = obj.xray

        # object properties
        if object_used:
            layout.prop(
                data,
                'isroot',
                text='Object',
                toggle=True,
                translate=False
            )

            if data.isroot:
                draw_object_props(layout, data)

        # details properties
        if details_used:
            layout.prop(
                data,
                'is_details',
                text='Details',
                toggle=True,
                translate=False
            )
            if data.is_details:
                draw_details_props(layout, context)

        # level properties
        if game_level_used:
            layout.prop(
                data,
                'is_level',
                text='Level',
                toggle=True,
                translate=False
            )
            if data.is_level:
                draw_level_props(layout, data)


classes = (
    XRAY_OT_prop_clip,
    XRAY_PT_object
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
