# blender modules
import bpy

# addon modules
from .. import ui
from .. import icons
from .. import menus
from .. import skls_browser
from .. import version_utils
from .. import ops
from .. import viewer

# plugin modules
from .. import obj
from .. import anm
from .. import bones
from .. import details
from .. import dm
from .. import err
from .. import level
from .. import ogf
from .. import omf
from .. import scene
from .. import skl


CATEGORY = 'X-Ray'


class XRAY_PT_skls_animations(ui.base.XRayPanel):
    'Contains open .skls file operator, animations list'
    bl_space_type = 'VIEW_3D'
    bl_label = 'Skls Browser'
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = CATEGORY
    if version_utils.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout

        obj = context.object
        active = False
        if not obj is None:
            if obj.type == 'ARMATURE':
                active = True
            else:
                layout.label(
                    text='Active object is not Armature!',
                    icon='ERROR'
                )
        else:
            layout.label(
                text='No active object!',
                icon='ERROR'
            )
        col = layout.column(align=True)
        col.active = active
        col.operator(
            operator=skls_browser.XRAY_OT_browse_skls_file.bl_idname,
            text='Open Skls File'
        )
        if not obj:
            return
        if hasattr(obj.xray, 'skls_browser'):
            if len(obj.xray.skls_browser.animations):
                layout.operator(skls_browser.XRAY_OT_close_skls_file.bl_idname)
            layout.template_list(
                listtype_name='XRAY_UL_skls_list_item',
                list_id='compact',
                dataptr=obj.xray.skls_browser,
                propname='animations',
                active_dataptr=obj.xray.skls_browser,
                active_propname='animations_index',
                rows=5
            )


class XRAY_PT_viewer(bpy.types.Panel):
    bl_label = 'Viewer'
    bl_space_type = 'VIEW_3D'
    bl_category = CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    if version_utils.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw_header(self, context):
        icon = icons.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        scn = context.scene
        viewer_folder = scn.get('viewer_folder')
        if viewer_folder:
            col.operator(
                viewer.XRAY_OT_viewer_close_folder.bl_idname,
                icon='X'
            )
            col.operator(
                viewer.XRAY_OT_viewer_preview_folder.bl_idname,
                icon='FILE_PARENT'
            )
            col.template_list(
                listtype_name='XRAY_UL_viewer_list_item',
                list_id='compact',
                dataptr=scn.xray.viewer,
                propname='files',
                active_dataptr=scn.xray.viewer,
                active_propname='files_index',
                rows=5
            )
        else:
            col.operator(
                viewer.XRAY_OT_viewer_open_folder.bl_idname,
                icon='FILE_FOLDER'
            )


class XRAY_PT_verify_tools(bpy.types.Panel):
    bl_label = 'Verify'
    bl_space_type = 'VIEW_3D'
    bl_category = CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    if version_utils.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw_header(self, context):
        icon = icons.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        data = context.scene.xray
        layout = self.layout
        layout.operator(
            ops.verify_uv.XRAY_OT_verify_uv.bl_idname,
            icon='GROUP_UVS'
        )


class XRAY_PT_transforms(bpy.types.Panel):
    bl_label = 'Transforms'
    bl_category = CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if version_utils.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw_header(self, context):
        icon = icons.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        lay = self.layout
        if not context.object:
            lay.label(text='No active object!', icon='ERROR')
            return
        data = context.object.xray
        column = lay.column()
        column.prop(data, 'position')
        column.prop(data, 'orientation')
        column = lay.column(align=True)
        column.operator(ops.transform_utils.XRAY_OT_update_blender_tranforms.bl_idname)
        column.operator(ops.transform_utils.XRAY_OT_update_xray_tranforms.bl_idname)
        column.operator(ops.transform_utils.XRAY_OT_copy_xray_tranforms.bl_idname)


class XRAY_PT_add(bpy.types.Panel):
    bl_label = 'Add'
    bl_category = CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if version_utils.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw_header(self, context):
        icon = icons.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        lay = self.layout
        lay.operator(ops.xray_camera.XRAY_OT_add_camera.bl_idname)


class XRAY_PT_batch_tools(bpy.types.Panel):
    bl_label = 'Batch Tools'
    bl_category = CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if version_utils.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw_header(self, context):
        icon = icons.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        data = context.scene.xray
        layout = self.layout
        column = layout.column(align=True)
        operator = column.operator(
            ops.material.XRAY_OT_colorize_materials.bl_idname, icon='COLOR'
        )
        operator.seed = data.materials_colorize_random_seed
        operator.power = data.materials_colorize_color_power
        column.prop(data, 'materials_colorize_random_seed', text='Seed')
        column.prop(data, 'materials_colorize_color_power', text='Power', slider=True)

        layout.operator(ops.action_utils.XRAY_OT_change_action_bake_settings.bl_idname)

        is_cycles = context.scene.render.engine == 'CYCLES'
        is_internal = context.scene.render.engine == 'BLENDER_RENDER'
        box = layout.box()
        box.label(text='Material Tools:')
        if box:
            column = box.column()
            split = version_utils.layout_split(column, 0.3)
            split.label(text='Mode:')
            split.prop(data, 'convert_materials_mode', text='')

            if not version_utils.IS_28:
                cycles_box = column.box()
                col_cycles = cycles_box.column()
                col_cycles.active = is_cycles or version_utils.IS_28
                internal_box = column.box()
                col_internal = internal_box.column()
                col_internal.active = is_internal and not version_utils.IS_28
                col_cycles.label(text='Cycles Settings:')
                split = version_utils.layout_split(col_cycles, 0.3)
                split.active = is_cycles
                split.label(text='Shader:')
                split.prop(data, 'convert_materials_shader_type', text='')
            else:
                col_cycles = column.column(align=True)
                col_cycles.active = is_cycles or version_utils.IS_28
                row = col_cycles.row(align=True)
                row.prop(data, 'change_materials_alpha', text='')
                row = row.row(align=True)
                row.active = data.change_materials_alpha
                row.prop(data, 'materials_set_alpha_mode', toggle=True)

            # specular
            row = col_cycles.row(align=True)
            row.prop(data, 'change_specular', text='')
            row = row.row(align=True)
            row.active = data.change_specular
            row.prop(data, 'shader_specular_value')
            # roughness
            row = col_cycles.row(align=True)
            row.prop(data, 'change_roughness', text='')
            row = row.row(align=True)
            row.active = data.change_roughness
            row.prop(data, 'shader_roughness_value')
            if version_utils.IS_28:
                # viewport roughness
                row = col_cycles.row(align=True)
                row.prop(data, 'change_viewport_roughness', text='')
                row = row.row(align=True)
                row.active = data.change_viewport_roughness
                row.prop(data, 'viewport_roughness_value')
            if not version_utils.IS_28:
                def draw_prop(change_prop, prop):
                    row = col_internal.row(align=True)
                    row.prop(data, change_prop, text='')
                    row = row.row(align=True)
                    row.active = getattr(data, change_prop)
                    row.prop(data, prop, toggle=True)
                col_internal.label(text='Internal Settings:')
                draw_prop('change_shadeless', 'use_shadeless')
                draw_prop('change_diffuse_intensity', 'diffuse_intensity')
                draw_prop('change_specular_intensity', 'specular_intensity')
                draw_prop('change_specular_hardness', 'specular_hardness')
                draw_prop('change_use_transparency', 'use_transparency')
                draw_prop('change_transparency_alpha', 'transparency_alpha')
            # operators
            column = box.column(align=True)
            if not version_utils.IS_28:
                column.operator(
                    ops.material.XRAY_OT_convert_to_cycles_material.bl_idname
                )
                col = column.column(align=True)
                col.active = is_cycles
                col.operator(
                    ops.material.XRAY_OT_convert_to_internal_material.bl_idname
                )
                if is_cycles:
                    text = 'Switch Render (Internal)'
                elif is_internal:
                    text = 'Switch Render (Cycles)'
                column.operator(
                    ops.material.XRAY_OT_switch_render.bl_idname,
                    text=text
                )
            column.operator(
                ops.shader_tools.XRAY_OT_change_shader_params.bl_idname
            )

        layout.operator(ops.object_tools.XRAY_OT_place_objects.bl_idname)


class XRAY_PT_custom_props(bpy.types.Panel):
    bl_label = 'Custom Properties'
    bl_category = CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if version_utils.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw_header(self, context):
        icon = icons.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        lay = self.layout
        scn = context.scene.xray
        split = version_utils.layout_split(lay, 0.4)
        split.label(text='Edit Data:')
        split.prop(scn, 'custom_properties_edit_data', text='')
        split = version_utils.layout_split(lay, 0.4)
        split.label(text='Edit Mode:')
        split.prop(scn, 'custom_properties_edit_mode', text='')
        lay.label(text='Set Custom Properties:')
        lay.operator(
            ops.custom_props_utils.XRAY_OT_set_xray_to_custom_props.bl_idname,
            text='X-Ray to Custom'
        )
        lay.operator(
            ops.custom_props_utils.XRAY_OT_set_custom_to_xray_props.bl_idname,
            text='Custom to X-Ray'
        )
        lay.label(text='Remove Custom Properties:')
        lay.operator(
            ops.custom_props_utils.XRAY_OT_remove_xray_custom_props.bl_idname,
            text='X-Ray'
        )
        lay.operator(
            ops.custom_props_utils.XRAY_OT_remove_all_custom_props.bl_idname,
            text='All'
        )


class XRAY_PT_armature_tools(bpy.types.Panel):
    bl_label = 'Armature Tools'
    bl_category = CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if version_utils.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw_header(self, context):
        icon = icons.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        lay = self.layout
        lay.operator(ops.bone_tools.XRAY_OT_resize_bones.bl_idname)


class XRAY_PT_import_operators(bpy.types.Panel):
    bl_label = 'Import'
    bl_category = CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if version_utils.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        enabled_import_operators = menus.get_enabled_operators(
            menus.import_draw_functions
        )
        return bool(enabled_import_operators)

    def draw_header(self, context):
        icon = icons.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        col = self.layout.column(align=True)
        preferences = version_utils.get_preferences()
        # object
        if preferences.enable_object_import:
            col.operator(obj.imp.ops.XRAY_OT_import_object.bl_idname, text='Object')
        # skls
        if preferences.enable_skls_import:
            col.operator(skl.ops.XRAY_OT_import_skls.bl_idname, text='Skls')
        # anm
        if preferences.enable_anm_import:
            col.operator(anm.ops.XRAY_OT_import_anm.bl_idname, text='Anm')
        # bones
        if preferences.enable_bones_import:
            col.operator(bones.ops.XRAY_OT_import_bones.bl_idname, text='Bones')
        # details
        if preferences.enable_details_import:
            col.operator(details.ops.XRAY_OT_import_details.bl_idname, text='Details')
        # dm
        if preferences.enable_dm_import:
            col.operator(dm.ops.XRAY_OT_import_dm.bl_idname, text='Dm')
        # scene
        if preferences.enable_level_import:
            col.operator(scene.ops.XRAY_OT_import_scene_selection.bl_idname, text='Scene')
        # omf
        if preferences.enable_omf_import:
            col.operator(omf.ops.XRAY_OT_import_omf.bl_idname, text='Omf')
        # level
        if preferences.enable_game_level_import:
            col.operator(level.ops.XRAY_OT_import_level.bl_idname, text='Level')
        # ogf
        if preferences.enable_ogf_import:
            col.operator(ogf.ops.XRAY_OT_import_ogf.bl_idname, text='Ogf')
        # err
        if preferences.enable_err_import:
            col.operator(err.ops.XRAY_OT_import_err.bl_idname, text='Err')


class XRAY_PT_export_operators(bpy.types.Panel):
    bl_label = 'Export'
    bl_category = CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if version_utils.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        enabled_export_operators = menus.get_enabled_operators(
            menus.export_draw_functions
        )
        return bool(enabled_export_operators)

    def draw_header(self, context):
        icon = icons.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        col = self.layout.column(align=True)
        preferences = version_utils.get_preferences()
        # object
        if preferences.enable_object_export:
            col.operator(obj.exp.ops.XRAY_OT_export_object.bl_idname, text='Object')
        # skls
        if preferences.enable_skls_export:
            col.operator(skl.ops.XRAY_OT_export_skls.bl_idname, text='Skls')
        # anm
        if preferences.enable_anm_export:
            col.operator(anm.ops.XRAY_OT_export_anm.bl_idname, text='Anm')
        # bones
        if preferences.enable_bones_export:
            col.operator(bones.ops.XRAY_OT_export_bones.bl_idname, text='Bones')
        # details
        if preferences.enable_details_export:
            col.operator(details.ops.XRAY_OT_export_details.bl_idname, text='Details')
        # dm
        if preferences.enable_dm_export:
            col.operator(dm.ops.XRAY_OT_export_dm.bl_idname, text='Dm')
        # scene
        if preferences.enable_level_export:
            col.operator(scene.ops.XRAY_OT_export_scene_selection.bl_idname, text='Scene')
        # omf
        if preferences.enable_omf_export:
            col.operator(omf.ops.XRAY_OT_export_omf.bl_idname, text='Omf')
        # level
        if preferences.enable_game_level_export:
            col.operator(level.ops.XRAY_OT_export_level.bl_idname, text='Level')
        # ogf
        if preferences.enable_ogf_export:
            col.operator(ogf.ops.XRAY_OT_export_ogf.bl_idname, text='Ogf')


classes = (
    XRAY_PT_skls_animations,
    XRAY_PT_viewer,
    XRAY_PT_transforms,
    XRAY_PT_add,
    XRAY_PT_verify_tools,
    XRAY_PT_batch_tools,
    XRAY_PT_custom_props,
    XRAY_PT_armature_tools,
    XRAY_PT_import_operators,
    XRAY_PT_export_operators
    
)


def register():
    for clas in classes:
        bpy.utils.register_class(clas)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
