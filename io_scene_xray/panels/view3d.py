# blender modules
import bpy

# addon modules
from .. import ui
from .. import icons
from .. import menus
from .. import skls_browser
from .. import version_utils
from .. import ops
from .. import rig
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
from .. import part


class XRAY_PT_skls_animations(ui.base.XRayPanel):
    'Contains open .skls file operator, animations list'
    bl_space_type = 'VIEW_3D'
    bl_label = 'Skls Browser'
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = ui.base.CATEGORY
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
                return
        else:
            layout.label(
                text='No active object!',
                icon='ERROR'
            )
            return
        col = layout.column(align=True)
        col.active = active
        col.operator(
            operator=skls_browser.XRAY_OT_browse_skls_file.bl_idname,
            text='Open Skls File',
            icon='FILE_FOLDER'
        )
        if hasattr(obj.xray, 'skls_browser'):
            if len(obj.xray.skls_browser.animations):
                col.operator(
                    skls_browser.XRAY_OT_close_skls_file.bl_idname,
                    icon='X'
                )
            col.template_list(
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
    bl_category = ui.base.CATEGORY
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
        viewer_folder = scn.xray.viewer.folder
        if viewer_folder:
            row = col.row(align=True)
            row.label(text=viewer_folder)
            row.operator(
                viewer.XRAY_OT_viewer_open_current_folder.bl_idname,
                text='',
                icon='FILE_FOLDER'
            )

            row = col.row(align=True)
            row.label(text='Sort:')
            row.prop(scn.xray.viewer, 'sort', expand=True)

            col_settings = col.column(align=True)
            col_settings.prop(scn.xray.viewer, 'sort_reverse')
            col_settings.prop(scn.xray.viewer, 'ignore_ext')
            col_settings.prop(scn.xray.viewer, 'show_size')
            col_settings.prop(scn.xray.viewer, 'group_by_ext')

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
            # select operators
            op_select_all = col.operator(
                viewer.XRAY_OT_viewer_select_files.bl_idname,
                text='Select All'
            )
            op_select_all.mode = 'SELECT_ALL'
            op_select_all = col.operator(
                viewer.XRAY_OT_viewer_select_files.bl_idname,
                text='Deselect All'
            )
            op_select_all.mode = 'DESELECT_ALL'
            op_select_all = col.operator(
                viewer.XRAY_OT_viewer_select_files.bl_idname,
                text='Invert Selection'
            )
            op_select_all.mode = 'INVERT_SELECTION'
            # import operators
            col.separator()
            import_row = col.row()
            import_col = import_row.column(align=True)
            op_import_active = import_col.operator(
                viewer.XRAY_OT_viewer_import_files.bl_idname,
                icon='IMPORT',
                text='Import Active File'
            )
            op_import_active.mode = 'IMPORT_ACTIVE'
            op_import_selected = import_col.operator(
                viewer.XRAY_OT_viewer_import_files.bl_idname,
                icon='IMPORT',
                text='Import Selected Files'
            )
            op_import_selected.mode = 'IMPORT_SELECTED'
            op_import_all = import_col.operator(
                viewer.XRAY_OT_viewer_import_files.bl_idname,
                icon='IMPORT',
                text='Import All Files'
            )
            op_import_all.mode = 'IMPORT_ALL'
        else:
            col.operator(
                viewer.XRAY_OT_viewer_open_folder.bl_idname,
                icon='FILE_FOLDER'
            )


class XRAY_PT_verify_tools(bpy.types.Panel):
    bl_label = 'Verify'
    bl_space_type = 'VIEW_3D'
    bl_category = ui.base.CATEGORY
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
        layout.operator(
            ops.verify_uv.XRAY_OT_verify_uv.bl_idname,
            icon='GROUP_UVS'
        )


class XRAY_PT_transforms(bpy.types.Panel):
    bl_label = 'Transforms'
    bl_category = ui.base.CATEGORY
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
    bl_category = ui.base.CATEGORY
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
        lay.operator(
            ops.xray_camera.XRAY_OT_add_camera.bl_idname,
            icon='CAMERA_DATA'
        )


class XRAY_PT_batch_tools(bpy.types.Panel):
    bl_label = 'Batch Tools'
    bl_category = ui.base.CATEGORY
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
        layout = self.layout
        column = layout.column(align=True)
        column.operator(
            ops.material.XRAY_OT_colorize_materials.bl_idname,
            icon='COLOR'
        )
        column.operator(
            ops.object_tools.XRAY_OT_colorize_objects.bl_idname,
            icon='COLOR'
        )
        column.operator(
            ops.action_utils.XRAY_OT_change_action_bake_settings.bl_idname,
            icon='ACTION'
        )
        if version_utils.IS_28:
            icon = 'LIGHTPROBE_GRID'
        else:
            icon = 'MANIPUL'
        column.operator(
            ops.object_tools.XRAY_OT_place_objects.bl_idname,
            icon=icon
        )
        column.operator(
            ops.shader_tools.XRAY_OT_change_shader_params.bl_idname,
            icon='MATERIAL'
        )
        column.operator(
            ops.fake_user_utils.XRAY_OT_change_fake_user.bl_idname,
            icon=version_utils.get_icon('FONT_DATA')
        )

        # 2.7x operators
        if not version_utils.IS_28:
            column.operator(
                ops.material.XRAY_OT_convert_to_cycles_material.bl_idname
            )
            column.operator(
                ops.material.XRAY_OT_convert_to_internal_material.bl_idname
            )

            if context.scene.render.engine == 'BLENDER_RENDER':
                switch_text = 'Switch to Cycles'
            elif context.scene.render.engine == 'CYCLES':
                switch_text = 'Switch to Internal'
            else:
                switch_text = 'Switch to Internal'

            column.operator(
                ops.material.XRAY_OT_switch_render.bl_idname,
                text=switch_text
            )
        column.operator(ops.action_utils.XRAY_OT_rename_actions.bl_idname)


class XRAY_PT_custom_props(bpy.types.Panel):
    bl_label = 'Custom Properties'
    bl_category = ui.base.CATEGORY
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
        lay.label(text='Set Custom Properties:')
        col = lay.column(align=True)
        col.operator(
            ops.custom_props_utils.XRAY_OT_set_xray_to_custom_props.bl_idname,
            text='X-Ray to Custom',
            icon='FORWARD'
        )
        col.operator(
            ops.custom_props_utils.XRAY_OT_set_custom_to_xray_props.bl_idname,
            text='Custom to X-Ray',
            icon='BACK'
        )
        lay.label(text='Remove Custom Properties:')
        row = lay.row(align=True)
        row.operator(
            ops.custom_props_utils.XRAY_OT_remove_xray_custom_props.bl_idname,
            text='X-Ray',
            icon='X'
        )
        row_danger = row.row(align=True)
        row_danger.alert = True
        row_danger.operator(
            ops.custom_props_utils.XRAY_OT_remove_all_custom_props.bl_idname,
            text='All',
            icon='CANCEL'
        )


class XRAY_PT_armature_tools(bpy.types.Panel):
    bl_label = 'Armature Tools'
    bl_category = ui.base.CATEGORY
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
        col = self.layout.column(align=True)
        col.operator(
            rig.connect_bones.XRAY_OT_create_connected_bones.bl_idname
        )
        col.operator(
            rig.create_ik.XRAY_OT_create_ik.bl_idname
        )
        col.operator(
            ops.bone_tools.XRAY_OT_resize_bones.bl_idname,
            icon='FULLSCREEN_ENTER'
        )
        col.operator(
            ops.armature_utils.XRAY_OT_link_bones.bl_idname
        )
        col.operator(
            ops.armature_utils.XRAY_OT_unlink_bones.bl_idname
        )
        col.label(text='Joint Limits:')
        col.operator(
            ops.joint_limits.XRAY_OT_convert_limits_to_constraints.bl_idname,
            icon='CONSTRAINT_BONE'
        )
        col.operator(
            ops.joint_limits.XRAY_OT_remove_limits_constraints.bl_idname,
            icon='X'
        )
        col.operator(
            ops.joint_limits.XRAY_OT_convert_ik_to_xray_limits.bl_idname
        )
        col.operator(
            ops.joint_limits.XRAY_OT_convert_xray_to_ik_limits.bl_idname
        )
        col_danger = col.column(align=True)
        col_danger.alert = True
        col_danger.operator(
            ops.joint_limits.XRAY_OT_clear_ik_limits.bl_idname
        )


class XRAY_PT_rig(bpy.types.Panel):
    bl_label = 'Rig'
    bl_category = ui.base.CATEGORY
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
        col = self.layout.column(align=True)
        if context.mode != 'POSE':
            col.label(
                text='Pose mode is not enabled!',
                icon='ERROR'
            )
            return
        obj = context.object
        bones = obj.pose.bones
        ik_fk_bones = []
        for bone in bones:
            ik_fk_prop = bone.get(rig.create_ik.IK_FK_PROP_NAME, None)
            if not ik_fk_prop is None:
                ik_fk_bones.append(bone)
        if not ik_fk_bones:
            col.label(
                text='Bones has not IK/FK properties!',
                icon='ERROR'
            )
            return
        for ik_bone in ik_fk_bones:
            col.prop(
                ik_bone,
                '["{}"]'.format(rig.create_ik.IK_FK_PROP_NAME),
                text=ik_bone['bone_category']
            )


class XRAY_PT_import_operators(bpy.types.Panel):
    bl_label = 'Import'
    bl_category = ui.base.CATEGORY
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
        for enable_prop_name, operator, label in menus.import_draw_functions:
            enable_prop = getattr(preferences, enable_prop_name)
            if enable_prop:
                col.operator(operator.bl_idname, text=label, icon='IMPORT')


class XRAY_PT_export_operators(bpy.types.Panel):
    bl_label = 'Export'
    bl_category = ui.base.CATEGORY
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
        for enable_prop_name, operator, label in menus.export_draw_functions:
            enable_prop = getattr(preferences, enable_prop_name)
            if enable_prop:
                col.operator(operator.bl_idname, text=label, icon='EXPORT')


classes = (
    XRAY_PT_skls_animations,
    XRAY_PT_viewer,
    XRAY_PT_transforms,
    XRAY_PT_add,
    XRAY_PT_verify_tools,
    XRAY_PT_batch_tools,
    XRAY_PT_custom_props,
    XRAY_PT_armature_tools,
    XRAY_PT_rig,
    XRAY_PT_import_operators,
    XRAY_PT_export_operators
)


def register():
    for clas in classes:
        bpy.utils.register_class(clas)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
