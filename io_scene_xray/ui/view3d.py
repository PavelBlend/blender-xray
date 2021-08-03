# blender modules
import bpy

# addon modules
from . import collapsible, icons
from .base import XRayPanel, build_label
from ..skls_browser import OpBrowseSklsFile, OpCloseSklsFile
from .. import prefs, plugin
from ..ops import custom_props_utils, action_utils, material
from ..version_utils import IS_28, assign_props, layout_split
from ..obj.imp import ops as obj_imp_ops
from ..obj.exp import ops as obj_exp_ops
from ..anm import ops as anm_ops
from ..bones import ops as bones_ops
from ..details import ops as details_ops
from ..dm import ops as dm_ops
from ..err import ops as err_ops
from ..level import ops as level_ops
from ..ogf import ops as ogf_ops
from ..omf import ops as omf_ops
from ..scene import ops as scene_ops
from ..skl import ops as skl_ops
from ..ops.transform_utils import (
    XRAY_OT_UpdateXRayObjectTranforms,
    XRAY_OT_UpdateBlenderObjectTranforms,
    XRAY_OT_CopyObjectTranforms
)
from ..ops import xray_camera, verify_uv


CATEGORY = 'X-Ray'


class XRAY_PT_skls_animations(XRayPanel):
    'Contains open .skls file operator, animations list'
    bl_space_type = 'VIEW_3D'
    bl_label = 'Skls Browser'
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = CATEGORY
    if IS_28:
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
        col.operator(operator=OpBrowseSklsFile.bl_idname, text='Open skls file...')
        if not obj:
            return
        if hasattr(obj.xray, 'skls_browser'):
            if len(obj.xray.skls_browser.animations):
                layout.operator(OpCloseSklsFile.bl_idname)
            layout.template_list(
                listtype_name='UI_UL_SklsList_item',
                list_id='compact',
                dataptr=obj.xray.skls_browser,
                propname='animations',
                active_dataptr=obj.xray.skls_browser,
                active_propname='animations_index',
                rows=5
            )


class XRAY_PT_VerifyToolsPanel(bpy.types.Panel):
    bl_label = 'Verify'
    bl_space_type = 'VIEW_3D'
    bl_category = CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    if IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw_header(self, _context):
        icon = icons.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        data = context.scene.xray
        layout = self.layout
        layout.operator(
            verify_uv.XRayVerifyUVOperator.bl_idname,
            icon='GROUP_UVS'
        )


class XRAY_PT_TransformsPanel(bpy.types.Panel):
    bl_label = 'Transforms'
    bl_category = CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw_header(self, _context):
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
        column.operator(XRAY_OT_UpdateBlenderObjectTranforms.bl_idname)
        column.operator(XRAY_OT_UpdateXRayObjectTranforms.bl_idname)
        column.operator(XRAY_OT_CopyObjectTranforms.bl_idname)


class XRAY_PT_AddPanel(bpy.types.Panel):
    bl_label = 'Add'
    bl_category = CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw_header(self, _context):
        icon = icons.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        lay = self.layout
        lay.operator(xray_camera.XRAY_OT_AddCamera.bl_idname)


class XRAY_PT_BatchToolsPanel(bpy.types.Panel):
    bl_label = 'Batch Tools'
    bl_category = CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw_header(self, _context):
        icon = icons.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        data = context.scene.xray
        layout = self.layout
        column = layout.column(align=True)
        operator = column.operator(
            material.MATERIAL_OT_colorize_materials.bl_idname, icon='COLOR'
        )
        operator.seed = data.materials_colorize_random_seed
        operator.power = data.materials_colorize_color_power
        column.prop(data, 'materials_colorize_random_seed', text='Seed')
        column.prop(data, 'materials_colorize_color_power', text='Power', slider=True)

        layout.operator(action_utils.XRAY_OT_ChangeActionBakeSettings.bl_idname)

        collapsible_text = 'Material Converter'
        if IS_28:
            collapsible_text = 'Principled Shader Utils'
        row, box = collapsible.draw(layout, 'test_key', text=collapsible_text)
        if box:
            split = layout_split(box, 0.3)
            split.label(text='Mode:')
            split.prop(context.scene.xray, 'convert_materials_mode', text='')
            utils_col = box.column(align=True)
            if not IS_28:
                utils_col.prop(context.scene.xray, 'convert_materials_shader_type')
                utils_col.operator('io_scene_xray.convert_to_cycles')
                utils_col.operator('io_scene_xray.convert_to_internal')
                if context.scene.render.engine == 'CYCLES':
                    text = 'Switch Render (Internal)'
                elif context.scene.render.engine == 'BLENDER_RENDER':
                    text = 'Switch Render (Cycles)'
                utils_col.operator('io_scene_xray.switch_render', text=text)
            else:
                row = utils_col.row(align=True)
                row.prop(context.scene.xray, 'change_materials_alpha', text='')
                row.prop(context.scene.xray, 'materials_set_alpha_mode', toggle=True)
            row = utils_col.row(align=True)
            row.prop(context.scene.xray, 'change_specular', text='')
            row.prop(context.scene.xray, 'shader_specular_value')
            row = utils_col.row(align=True)
            row.prop(context.scene.xray, 'change_roughness', text='')
            row.prop(context.scene.xray, 'shader_roughness_value')
            box.operator('io_scene_xray.change_shader_params')


class XRAY_PT_CustomPropertiesUtilsPanel(bpy.types.Panel):
    bl_label = 'Custom Properties'
    bl_category = CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw_header(self, _context):
        icon = icons.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        lay = self.layout
        scn = context.scene.xray
        split = layout_split(lay, 0.4)
        split.label(text='Edit Data:')
        split.prop(scn, 'custom_properties_edit_data', text='')
        split = layout_split(lay, 0.4)
        split.label(text='Edit Mode:')
        split.prop(scn, 'custom_properties_edit_mode', text='')
        lay.label(text='Set Custom Properties:')
        lay.operator(
            custom_props_utils.XRAY_OT_SetXRayToCustomProperties.bl_idname,
            text='X-Ray to Custom'
        )
        lay.operator(
            custom_props_utils.XRAY_OT_SetCustomToXRayProperties.bl_idname,
            text='Custom to X-Ray'
        )
        lay.label(text='Remove Custom Properties:')
        lay.operator(
            custom_props_utils.XRAY_OT_RemoveXRayCustomProperties.bl_idname,
            text='X-Ray'
        )
        lay.operator(
            custom_props_utils.XRAY_OT_RemoveAllCustomProperties.bl_idname,
            text='All'
        )


class XRAY_PT_ImportPluginsPanel(bpy.types.Panel):
    bl_label = 'Import'
    bl_category = CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        enabled_import_operators = plugin.get_enabled_operators(
            plugin.import_draw_functions
        )
        return bool(enabled_import_operators)

    def draw_header(self, _context):
        icon = icons.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        lay = self.layout
        preferences = prefs.utils.get_preferences()
        # object
        if preferences.enable_object_import:
            lay.operator(obj_imp_ops.OpImportObject.bl_idname, text='Object')
        # skls
        if preferences.enable_skls_import:
            lay.operator(skl_ops.OpImportSkl.bl_idname, text='Skls')
        # anm
        if preferences.enable_anm_import:
            lay.operator(anm_ops.OpImportAnm.bl_idname, text='Anm')
        # bones
        if preferences.enable_bones_import:
            lay.operator(bones_ops.IMPORT_OT_xray_bones.bl_idname, text='Bones')
        # details
        if preferences.enable_details_import:
            lay.operator(details_ops.OpImportDetails.bl_idname, text='Details')
        # dm
        if preferences.enable_dm_import:
            lay.operator(dm_ops.OpImportDM.bl_idname, text='Dm')
        # scene
        if preferences.enable_level_import:
            lay.operator(scene_ops.OpImportLevelScene.bl_idname, text='Scene')
        # omf
        if preferences.enable_omf_import:
            lay.operator(omf_ops.IMPORT_OT_xray_omf.bl_idname, text='Omf')
        # level
        if preferences.enable_game_level_import:
            lay.operator(level_ops.IMPORT_OT_xray_level.bl_idname, text='Level')
        # err
        if preferences.enable_err_import:
            lay.operator(err_ops.OpImportERR.bl_idname, text='Err')


class XRAY_PT_ExportPluginsPanel(bpy.types.Panel):
    bl_label = 'Export'
    bl_category = CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        enabled_export_operators = plugin.get_enabled_operators(
            plugin.export_draw_functions
        )
        return bool(enabled_export_operators)

    def draw_header(self, _context):
        icon = icons.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        lay = self.layout
        preferences = prefs.utils.get_preferences()
        # object
        if preferences.enable_object_export:
            lay.operator(obj_exp_ops.OpExportObjects.bl_idname, text='Object')
        # skls
        if preferences.enable_skls_export:
            lay.operator(skl_ops.OpExportSkls.bl_idname, text='Skls')
        # anm
        if preferences.enable_anm_export:
            lay.operator(anm_ops.OpExportAnm.bl_idname, text='Anm')
        # bones
        if preferences.enable_bones_export:
            lay.operator(bones_ops.EXPORT_OT_xray_bones_batch.bl_idname, text='Bones')
        # details
        if preferences.enable_details_export:
            lay.operator(details_ops.OpExportDetails.bl_idname, text='Details')
        # dm
        if preferences.enable_dm_export:
            lay.operator(dm_ops.OpExportDMs.bl_idname, text='Dm')
        # scene
        if preferences.enable_level_export:
            lay.operator(scene_ops.OpExportLevelScene.bl_idname, text='Scene')
        # omf
        if preferences.enable_omf_export:
            lay.operator(omf_ops.EXPORT_OT_xray_omf.bl_idname, text='Omf')
        # level
        if preferences.enable_game_level_export:
            lay.operator(level_ops.EXPORT_OT_xray_level.bl_idname, text='Level')
        # ogf
        if preferences.enable_ogf_export:
            lay.operator(ogf_ops.OpExportOgf.bl_idname, text='Ogf')


classes = (
    XRAY_PT_skls_animations,
    XRAY_PT_TransformsPanel,
    XRAY_PT_AddPanel,
    XRAY_PT_VerifyToolsPanel,
    XRAY_PT_BatchToolsPanel,
    XRAY_PT_CustomPropertiesUtilsPanel,
    XRAY_PT_ImportPluginsPanel,
    XRAY_PT_ExportPluginsPanel
    
)


def register():
    for clas in classes:
        bpy.utils.register_class(clas)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
