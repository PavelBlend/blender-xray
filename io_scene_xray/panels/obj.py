# standart modules
import os

# blender modules
import bpy

# addon modules
from .. import ui
from .. import utils
from .. import ops
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


class XRAY_UL_motion_list(bpy.types.UIList):
    bl_idname = 'XRAY_UL_motion_list'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        data = context.active_object.xray
        motion = data.motions_collection[index]

        if data.motions_collection_index == index:
            icon = 'CHECKBOX_HLT'
        else:
            icon = 'CHECKBOX_DEHLT'

        row = layout.row()
        row.label(text='', icon=icon)

        if data.show_motions_names in ('ACTION', 'BOTH'):
            row.prop_search(motion, 'name', bpy.data, 'actions', text='')

        if data.show_motions_names == 'BOTH':
            if data.use_custom_motion_names:
                row.prop(motion, 'export_name', icon_only=True)
            else:
                row.label(
                    text='Enable the "Custom Names" option',
                    icon='ERROR'
                )

        if data.show_motions_names == 'EXPORT':
            if motion.export_name:
                row.label(text=motion.export_name)
            else:
                row.label(text=motion.name)


def draw_motion_list_elements(layout):
    layout.operator(
        ops.motion.XRAY_OT_add_all_actions.bl_idname,
        text='',
        icon='ACTION'
    )
    layout.operator(
        ops.motion.XRAY_OT_clean_actions.bl_idname,
        text='',
        icon='BRUSH_DATA'
    )
    layout.operator(
        ops.motion.XRAY_OT_remove_all_actions.bl_idname,
        text='',
        icon='X'
    )
    layout.operator(
        ops.motion.XRAY_OT_copy_actions.bl_idname,
        text='',
        icon='COPYDOWN'
    )
    layout.operator(
        ops.motion.XRAY_OT_paste_actions.bl_idname,
        text='',
        icon='PASTEDOWN'
    )
    layout.operator(
        ops.motion.XRAY_OT_sort_actions.bl_idname,
        text='',
        icon='SORTALPHA'
    )


class XRAY_OT_remove_all_motion_refs(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.remove_all_motion_refs'
    bl_label = 'Remove All'
    bl_description = 'Remove all motion references'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False
        data = obj.xray
        refs_count = len(data.motionrefs_collection)
        return bool(refs_count)

    def execute(self, context):
        obj = context.active_object
        obj.xray.motionrefs_collection.clear()
        utils.draw.redraw_areas()
        return {'FINISHED'}


class XRAY_OT_copy_motion_refs_list(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.copy_motion_refs_list'
    bl_label = 'Copy Motion References'
    bl_description = 'Copy motion references list to clipboard'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False
        return True

    def execute(self, context):
        obj = context.active_object
        lines = []
        saved_refs = set()
        for ref in obj.xray.motionrefs_collection:
            name = ref.name
            if not name:
                continue
            if name in saved_refs:
                continue
            unique_chars = set(name)
            if unique_chars == {' ', }:
                continue
            lines.append(name)
            saved_refs.add(name)
        bpy.context.window_manager.clipboard = '\n'.join(lines)
        return {'FINISHED'}


class XRAY_OT_paste_motion_refs_list(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.paste_motion_refs_list'
    bl_label = 'Past Motion References'
    bl_description = 'Paste motion references list from clipboard'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False
        return True

    def execute(self, context):
        obj = context.active_object
        refs = obj.xray.motionrefs_collection
        used_refs = {ref.name for ref in obj.xray.motionrefs_collection}
        refs_data = bpy.context.window_manager.clipboard
        for line in refs_data.split('\n'):
            if not line:
                continue
            if line in used_refs:
                continue
            unique_chars = set(line)
            if unique_chars == {' ', }:
                continue
            ref = refs.add()
            ref.name = line
        utils.draw.redraw_areas()
        return {'FINISHED'}


class XRAY_OT_sort_motion_refs_list(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.sort_motion_refs_list'
    bl_label = 'Sort Motion References'
    bl_description = 'Sort motion references list'
    bl_options = {'UNDO'}

    sort_reverse = bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False
        return True

    def draw(self, context):
        lay = self.layout
        lay.prop(self, 'sort_reverse', text='Reverse Sort', toggle=True)

    def execute(self, context):
        obj = context.active_object
        refs = obj.xray.motionrefs_collection

        used_refs = [ref.name for ref in refs]
        used_refs.sort()

        if self.sort_reverse:
            used_refs.reverse()

        refs.clear()

        for ref in used_refs:
            elem = refs.add()
            elem.name = ref

        utils.draw.redraw_areas()

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_add_motion_ref_from_file(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.add_motion_ref_from_file'
    bl_label = 'Add Motion Reference'
    bl_description = 'Add motion reference from file path'
    bl_options = {'UNDO'}

    init = False

    filter_glob = bpy.props.StringProperty(
        default='*.omf',
        options={'HIDDEN'}
    )
    directory = bpy.props.StringProperty(
        subtype='DIR_PATH',
        options={'SKIP_SAVE'}
    )
    files = bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False
        return True

    def draw(self, context):
        if not self.init:
            self.init = True
            space = context.space_data
            params = space.params
            prefs = utils.version.get_preferences()
            meshes_folders = utils.ie.get_pref_paths('meshes_folder')

            for mshs_folder in meshes_folders:
                if mshs_folder and os.path.exists(mshs_folder):

                    if isinstance(params.directory, bytes):
                        mshs_folder = bytes(mshs_folder, encoding='utf-8')

                    if not params.directory.startswith(mshs_folder):
                        params.directory = mshs_folder

    def execute(self, context):
        obj = context.active_object
        refs = obj.xray.motionrefs_collection
        meshes_folders = utils.ie.get_pref_paths('meshes_folder')

        mshs_folder = None
        for val in meshes_folders:
            if val:
                mshs_folder = val

        if not mshs_folder:
            self.report({'WARNING'}, 'Meshes folder not specified!')
            return {'FINISHED'}

        fail_count = 0
        for file in self.files:
            if not file.name.endswith('.omf'):
                continue
            file_path = os.path.join(self.directory, file.name)
            if not file_path.startswith(mshs_folder):
                fail_count += 1
                continue
            relative_path = file_path[len(mshs_folder) : ]
            motion_ref = os.path.splitext(relative_path)[0]
            if not motion_ref in refs:
                ref = refs.add()
                ref.name = motion_ref

        if fail_count:
            self.report(
                {'WARNING'},
                'Could not add {} references!'.format(fail_count)
            )

        utils.draw.redraw_areas()

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def draw_motion_refs_elements(layout):
    layout.operator(XRAY_OT_remove_all_motion_refs.bl_idname, text='', icon='X')
    layout.operator(XRAY_OT_copy_motion_refs_list.bl_idname, text='', icon='COPYDOWN')
    layout.operator(XRAY_OT_paste_motion_refs_list.bl_idname, text='', icon='PASTEDOWN')
    layout.operator(XRAY_OT_sort_motion_refs_list.bl_idname, text='', icon='SORTALPHA')
    layout.operator(XRAY_OT_add_motion_ref_from_file.bl_idname, text='', icon='FILE_FOLDER')


def details_draw_function(self, context):
    box = self.layout.box()

    if not (context.active_object.type in {'MESH', 'EMPTY'}):
        box.label(
            text='Active object is not a mesh or empty',
            icon='ERROR'
        )
        return

    if context.active_object.type == 'MESH':

        model = context.active_object.xray.detail.model

        col = box.column(align=True)
        col.label(text='Detail Model Properties:')

        col.prop(model, 'no_waving', text='No Waving', toggle=True)
        col.prop(model, 'min_scale', text='Min Scale')
        col.prop(model, 'max_scale', text='Max Scale')
        col.prop(model, 'index', text='Detail Index')
        col.prop(model, 'color', text='')

    elif context.active_object.type == 'EMPTY':

        slots = context.active_object.xray.detail.slots

        box.label(text='Level Details Properties:')

        split = utils.version.layout_split(box, 0.4, align=True)
        split.label(text='Meshes Object:')
        split.prop_search(
            slots,
            'meshes_object',
            bpy.data,
            'objects',
            text=''
        )

        split = utils.version.layout_split(box, 0.4, align=True)
        split.label(text='Slots Base Object:')
        split.prop_search(
            slots,
            'slots_base_object',
            bpy.data,
            'objects',
            text=''
        )

        split = utils.version.layout_split(box, 0.4, align=True)
        split.label(text='Slots Top Object:')
        split.prop_search(
            slots,
            'slots_top_object',
            bpy.data,
            'objects',
            text=''
        )

        _, box_ = ui.collapsible.draw(
            box, 'object:lighting', 'Lighting Coefficients'
        )

        if box_:

            ligthing = slots.ligthing
            box_.label(text='Format:')
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
            box, 'object:slots', 'Slots Meshes Indices'
        )

        if box_:
            for mesh_index in range(4):
                box_.prop_search(
                    slots.meshes,
                    'mesh_{}'.format(mesh_index),
                    bpy.data,
                    'images',
                    text='Mesh {}'.format(mesh_index)
                )

        box.operator(formats.details.ops.XRAY_OT_pack_details_images.bl_idname)


def draw_split_prop(layout, owner, prop, label):
    split = utils.version.layout_split(layout, 0.333, align=True)
    split.label(text=label+':')
    split.prop(owner, prop, text='')


def draw_split_prop_search(layout, owner, prop, label, search_owner, search_prop):
    split = utils.version.layout_split(layout, 0.333, align=True)
    split.label(text=label+':')
    split.prop_search(owner, prop, search_owner, search_prop, text='')


def level_draw_function(layout, data):
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
        prefs.enable_part_export or
        prefs.enable_omf_export or
        prefs.enable_ogf_export
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
        preferences = utils.version.get_preferences()
        object_used, details_used, game_level_used = get_used(preferences)
        return object_used or details_used or game_level_used

    def draw(self, context):
        preferences = utils.version.get_preferences()
        object_used, details_used, game_level_used = get_used(preferences)

        layout = self.layout
        data = context.active_object.xray
        if object_used:
            layout.prop(
                data,
                'isroot',
                text='Object',
                toggle=True,
                translate=False
            )

            if data.isroot:
                object_box = layout.box()
                if not data.flags_use_custom:
                    split = utils.version.layout_split(object_box, 0.333)
                    split.label(text='Type:')
                    split.prop(data, 'flags_simple', text='')
                else:
                    # type
                    split = utils.version.layout_split(object_box, 0.333)
                    split.label(text='Type:')
                    split.prop(data, 'flags_simple', text='')
                    # static/dynamic
                    row = object_box.row(align=True)
                    row.prop(data, 'flags_custom_type', expand=True)
                    # flags
                    col = object_box.column(align=True)
                    row = col.row(align=True)
                    row.prop(data, 'flags_custom_progressive', text='Progressive', toggle=True)
                    row.prop(data, 'flags_custom_lod', text='LOD', toggle=True)
                    row.prop(data, 'flags_custom_hom', text='HOM', toggle=True)
                    row = col.row(align=True)
                    row.prop(data, 'flags_custom_musage', text='Multiple Usage', toggle=True)
                    row.prop(data, 'flags_custom_soccl', text='Sound Occluder', toggle=True)
                object_box.prop(data, 'flags_custom_hqexp', text='HQ Export')
                split = utils.version.layout_split(object_box, 0.333)
                split.label(text='LOD Reference:')
                split.prop(data, 'lodref', text='')
                split = utils.version.layout_split(object_box, 0.333)
                split.label(text='Export Path:')
                split.prop(data, 'export_path', text='')
                row, box = ui.collapsible.draw(
                    object_box,
                    'object:userdata',
                    'User Data',
                    enabled=data.userdata != '',
                    icon='VIEWZOOM'
                )
                XRAY_OT_prop_clip.drawall(row, 'object.xray.userdata', data.userdata)
                if box:
                    if not data.userdata:
                        ui.collapsible.XRAY_OT_collaps.set_value(
                            'object:userdata',
                            False
                        )
                    else:
                        box = box.column(align=True)
                        for line in data.userdata.splitlines():
                            box.label(text=line)

                if data.motions:
                    split = object_box.split()
                    split.alert = True
                    split.prop(data, 'motions')
                _, box = ui.collapsible.draw(
                    object_box,
                    'object:motions',
                    'Motions ({})'.format(len(data.motions_collection))
                )
                if box:
                    col = box.column(align=True)
                    col.prop(data, 'play_active_motion', toggle=True, icon='PLAY')
                    col.prop(data, 'use_custom_motion_names', toggle=True, icon='SORTALPHA')
                    names_row = col.row()
                    names_row.label(text='Show:')
                    names_row.prop(data, 'show_motions_names', expand=True)
                    split = utils.version.layout_split(col, 0.333)
                    split.label(text='Dependency:')
                    split.prop_search(
                        data,
                        'dependency_object',
                        bpy.data,
                        'objects',
                        text=''
                    )
                    row = box.row()
                    row.template_list(
                        'XRAY_UL_motion_list', 'name',
                        data, 'motions_collection',
                        data, 'motions_collection_index',
                        rows=9
                    )
                    col = row.column(align=True)
                    ui.list_helper.draw_list_ops(
                        col,
                        data,
                        'motions_collection',
                        'motions_collection_index',
                        custom_elements_func=draw_motion_list_elements
                    )

                if data.motionrefs:
                    split = object_box.split()
                    split.alert = True
                    split.prop(data, 'motionrefs')
                _, box = ui.collapsible.draw(
                    object_box,
                    'object:motionsrefs',
                    'Motion Refs ({})'.format(len(data.motionrefs_collection))
                )
                if box:
                    box.prop(data, 'load_active_motion_refs', toggle=True)
                    if data.load_active_motion_refs:
                        row = box.row()
                        row.label(text='Format:')
                        row.prop(data.motions_browser, 'file_format', expand=True)
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
                    col = row.column(align=True)
                    ui.list_helper.draw_list_ops(
                        col,
                        data,
                        'motionrefs_collection',
                        'motionrefs_collection_index',
                        custom_elements_func=draw_motion_refs_elements
                    )

                _, box = ui.collapsible.draw(
                    object_box,
                    'object:revision',
                    'Revision'
                )
                if box:
                    # owner
                    split = utils.version.layout_split(box, 0.35)
                    split.label(text='Owner Name:')
                    split.prop(data.revision, 'owner', text='')
                    # created time
                    split = utils.version.layout_split(box, 0.35)
                    split.label(text='Created Time:')
                    split.prop(data.revision, 'ctime_str', text='')
                    # modif name
                    split = utils.version.layout_split(box, 0.35)
                    split.label(text='Moder Name:')
                    split.label(text=data.revision.moder)
                    # modified time
                    split = utils.version.layout_split(box, 0.35)
                    split.label(text='Modified Time:')
                    split.label(text=data.revision.mtime_str)
                    # time formats
                    subbox = box.box()
                    split = utils.version.layout_split(subbox, 0.25)
                    split.label(text='')
                    split.label(text='Time Formats:', icon='INFO')
                    subbox.label(text='Year.Month.Day Hours:Minutes')
                    subbox.label(text='Year.Month.Day')

        if details_used:
            layout.prop(
                data,
                'is_details',
                text='Details',
                toggle=True,
                translate=False
            )
            if data.is_details:
                details_draw_function(self, context)

        if game_level_used:
            layout.prop(
                data,
                'is_level',
                text='Level',
                toggle=True,
                translate=False
            )
            if data.is_level:
                level_draw_function(layout, data)


classes = (
    XRAY_OT_prop_clip,
    XRAY_UL_motion_list,
    XRAY_OT_remove_all_motion_refs,
    XRAY_OT_copy_motion_refs_list,
    XRAY_OT_paste_motion_refs_list,
    XRAY_OT_sort_motion_refs_list,
    XRAY_OT_add_motion_ref_from_file,
    XRAY_PT_object
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
