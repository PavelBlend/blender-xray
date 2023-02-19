# blender modules
import bpy

# addon modules
from .. import ui
from .. import menus
from .. import utils
from .. import ops


class XRAY_PT_update(ui.base.XRayPanel):
    bl_label = 'Update'
    bl_space_type = 'VIEW_3D'
    bl_category = ui.base.CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    if utils.version.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout
        layout.operator(
            ops.update.XRAY_OT_check_update.bl_idname,
            icon='WORLD'
        )


class XRAY_PT_skls_animations(ui.base.XRayPanel):
    'Contains open .skls file operator, animations list'
    bl_space_type = 'VIEW_3D'
    bl_label = 'Skls Browser'
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = ui.base.CATEGORY
    if utils.version.IS_28:
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
            operator=ops.skls_browser.XRAY_OT_browse_skls_file.bl_idname,
            text='Open Skls File',
            icon='FILE_FOLDER'
        )
        if hasattr(obj.xray, 'skls_browser'):
            has_anims = len(obj.xray.skls_browser.animations)
            if has_anims:
                col.operator(
                    ops.skls_browser.XRAY_OT_close_skls_file.bl_idname,
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

            if not has_anims:
                return

            # select
            select_op_class = ops.skls_browser.XRAY_OT_skls_browser_select
            row = col.row(align=True)
            row.label(text='Select:')

            select_op = row.operator(select_op_class.bl_idname, text='All')
            select_op.mode = 'ALL'

            select_op = row.operator(select_op_class.bl_idname, text='None')
            select_op.mode = 'NONE'

            select_op = row.operator(select_op_class.bl_idname, text='Invert')
            select_op.mode = 'INVERT'

            # import
            import_op_class = ops.skls_browser.XRAY_OT_skls_browser_import
            row = col.row(align=True)
            row.label(text='Import:')

            imp_op = row.operator(import_op_class.bl_idname, text='Active')
            imp_op.mode = 'ACTIVE'

            imp_op = row.operator(import_op_class.bl_idname, text='Selected')
            imp_op.mode = 'SELECTED'

            imp_op = row.operator(import_op_class.bl_idname, text='All')
            imp_op.mode = 'ALL'


class XRAY_PT_viewer(ui.base.XRayPanel):
    bl_label = 'Viewer'
    bl_space_type = 'VIEW_3D'
    bl_category = ui.base.CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    if utils.version.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        scn = context.scene
        viewer_folder = scn.xray.viewer.folder
        if viewer_folder:
            row = col.row(align=True)
            row.label(text=viewer_folder)
            row.operator(
                ops.viewer.XRAY_OT_viewer_open_current_folder.bl_idname,
                text='',
                icon='FILE_FOLDER'
            )

            row = col.row(align=True)
            row.label(text='Sort:')
            row.prop(scn.xray.viewer, 'sort', expand=True)

            col_settings = col.column(align=True)

            # formats
            col_settings.label(text='Use Formats:')
            row = col_settings.row(align=True)
            row.prop(scn.xray.viewer, 'use_object', toggle=True)
            row.prop(scn.xray.viewer, 'use_ogf', toggle=True)
            row.prop(scn.xray.viewer, 'use_dm', toggle=True)
            row.prop(scn.xray.viewer, 'use_details', toggle=True)

            col_settings.prop(scn.xray.viewer, 'import_motions')
            col_settings.prop(scn.xray.viewer, 'sort_reverse')
            col_settings.prop(scn.xray.viewer, 'ignore_ext')
            col_settings.prop(scn.xray.viewer, 'show_size')
            col_settings.prop(scn.xray.viewer, 'group_by_ext')

            col.operator(
                ops.viewer.XRAY_OT_viewer_close_folder.bl_idname,
                icon='X'
            )
            col.operator(
                ops.viewer.XRAY_OT_viewer_preview_folder.bl_idname,
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
            row = col.row(align=True)
            row.label(text='Select:')
            op_select_all = row.operator(
                ops.viewer.XRAY_OT_viewer_select_files.bl_idname,
                text='All'
            )
            op_select_all.mode = 'SELECT_ALL'
            op_select_all = row.operator(
                ops.viewer.XRAY_OT_viewer_select_files.bl_idname,
                text='None'
            )
            op_select_all.mode = 'DESELECT_ALL'
            op_select_all = row.operator(
                ops.viewer.XRAY_OT_viewer_select_files.bl_idname,
                text='Invert'
            )
            op_select_all.mode = 'INVERT_SELECTION'
            # import operators
            row = col.row(align=True)
            row.label(text='Import:')
            op_import_active = row.operator(
                ops.viewer.XRAY_OT_viewer_import_files.bl_idname,
                text='Active'
            )
            op_import_active.mode = 'IMPORT_ACTIVE'
            op_import_selected = row.operator(
                ops.viewer.XRAY_OT_viewer_import_files.bl_idname,
                text='Selected'
            )
            op_import_selected.mode = 'IMPORT_SELECTED'
            op_import_all = row.operator(
                ops.viewer.XRAY_OT_viewer_import_files.bl_idname,
                text='All'
            )
            op_import_all.mode = 'IMPORT_ALL'
        else:
            col.operator(
                ops.viewer.XRAY_OT_viewer_open_folder.bl_idname,
                icon='FILE_FOLDER'
            )


class XRAY_PT_verify_tools(ui.base.XRayPanel):
    bl_label = 'Verify'
    bl_space_type = 'VIEW_3D'
    bl_category = ui.base.CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    if utils.version.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout
        layout.operator(
            ops.verify.XRAY_OT_verify_uv.bl_idname,
            icon='GROUP_UVS'
        )


class XRAY_PT_transforms(ui.base.XRayPanel):
    bl_label = 'Transforms'
    bl_category = ui.base.CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if utils.version.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

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
        column.operator(ops.transform.XRAY_OT_update_blender_tranforms.bl_idname)
        column.operator(ops.transform.XRAY_OT_update_xray_tranforms.bl_idname)
        column.operator(ops.transform.XRAY_OT_copy_xray_tranforms.bl_idname)


class XRAY_PT_add(ui.base.XRayPanel):
    bl_label = 'Add'
    bl_category = ui.base.CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if utils.version.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw(self, context):
        lay = self.layout
        lay.operator(
            ops.add.XRAY_OT_add_camera.bl_idname,
            icon='CAMERA_DATA'
        )


class XRAY_PT_props_tools(ui.base.XRayPanel):
    bl_label = 'Props Tools'
    bl_space_type = 'VIEW_3D'
    bl_category = ui.base.CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    if utils.version.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.operator(ops.props_tools.XRAY_OT_change_object_type.bl_idname)
        col.operator(ops.props_tools.XRAY_OT_change_hq_export.bl_idname)
        col.operator(ops.props_tools.XRAY_OT_change_userdata.bl_idname)
        col.operator(ops.props_tools.XRAY_OT_change_lod_ref.bl_idname)
        col.operator(ops.props_tools.XRAY_OT_change_motion_refs.bl_idname)


class XRAY_PT_batch_tools(ui.base.XRayPanel):
    bl_label = 'Batch Tools'
    bl_category = ui.base.CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if utils.version.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        column.operator(
            ops.material.XRAY_OT_colorize_materials.bl_idname,
            icon='COLOR'
        )
        column.operator(
            ops.obj.XRAY_OT_colorize_objects.bl_idname,
            icon='COLOR'
        )
        column.operator(
            ops.action.XRAY_OT_change_action_bake_settings.bl_idname,
            icon='ACTION'
        )
        if utils.version.IS_28:
            icon = 'LIGHTPROBE_GRID'
        else:
            icon = 'MANIPUL'
        column.operator(
            ops.obj.XRAY_OT_place_objects.bl_idname,
            icon=icon
        )
        column.operator(
            ops.shader.XRAY_OT_change_shader_params.bl_idname,
            icon='MATERIAL'
        )
        column.operator(
            ops.fake_user.XRAY_OT_change_fake_user.bl_idname,
            icon=utils.version.get_icon('FONT_DATA')
        )

        # 2.7x operators
        if not utils.version.IS_28:
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
        column.operator(ops.action.XRAY_OT_rename_actions.bl_idname)

        if utils.version.has_asset_browser():
            column.operator(ops.obj.XRAY_OT_set_asset_author.bl_idname)


class XRAY_PT_custom_props(ui.base.XRayPanel):
    bl_label = 'Custom Properties'
    bl_category = ui.base.CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if utils.version.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw(self, context):
        lay = self.layout
        lay.label(text='Set Custom Properties:')
        col = lay.column(align=True)
        col.operator(
            ops.custom_props.XRAY_OT_set_xray_to_custom_props.bl_idname,
            text='X-Ray to Custom',
            icon='FORWARD'
        )
        col.operator(
            ops.custom_props.XRAY_OT_set_custom_to_xray_props.bl_idname,
            text='Custom to X-Ray',
            icon='BACK'
        )
        lay.label(text='Remove Custom Properties:')
        row = lay.row(align=True)
        row.operator(
            ops.custom_props.XRAY_OT_remove_xray_custom_props.bl_idname,
            text='X-Ray',
            icon='X'
        )
        row_danger = row.row(align=True)
        row_danger.alert = True
        row_danger.operator(
            ops.custom_props.XRAY_OT_remove_all_custom_props.bl_idname,
            text='All',
            icon='CANCEL'
        )


class XRAY_PT_armature_tools(ui.base.XRayPanel):
    bl_label = 'Armature Tools'
    bl_category = ui.base.CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if utils.version.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw(self, context):
        col = self.layout.column(align=True)
        col.operator(
            ops.rig.connect_bones.XRAY_OT_create_connected_bones.bl_idname
        )
        col.operator(
            ops.rig.create_ik.XRAY_OT_create_ik.bl_idname
        )
        col.operator(
            ops.bone.XRAY_OT_resize_bones.bl_idname,
            icon='FULLSCREEN_ENTER'
        )
        col.operator(
            ops.armature.XRAY_OT_link_bones.bl_idname
        )
        col.operator(
            ops.armature.XRAY_OT_unlink_bones.bl_idname
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


class XRAY_PT_rig(ui.base.XRayPanel):
    bl_label = 'Rig'
    bl_category = ui.base.CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if utils.version.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

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
            ik_fk_prop = bone.get(ops.rig.create_ik.IK_FK_PROP_NAME, None)
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
                '["{}"]'.format(ops.rig.create_ik.IK_FK_PROP_NAME),
                text=ik_bone['bone_category']
            )


class XRAY_PT_import_operators(ui.base.XRayPanel):
    bl_label = 'Import'
    bl_category = ui.base.CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if utils.version.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        enabled_import_operators = menus.get_enabled_operators(
            menus.import_ops,
            'import'
        )
        return bool(enabled_import_operators)

    def draw(self, context):
        col = self.layout.column(align=True)
        preferences = utils.version.get_preferences()
        for operator, label in menus.import_ops:
            enable_prop_name = 'enable_{}_import'.format(label.lower())
            enable_prop = getattr(preferences, enable_prop_name)
            if enable_prop:
                col.operator(operator.bl_idname, text=label, icon='IMPORT')


class XRAY_PT_export_operators(ui.base.XRayPanel):
    bl_label = 'Export'
    bl_category = ui.base.CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if utils.version.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        enabled_export_operators = menus.get_enabled_operators(
            menus.export_ops,
            'export'
        )
        return bool(enabled_export_operators)

    def draw(self, context):
        col = self.layout.column(align=True)
        preferences = utils.version.get_preferences()
        for operator, label in menus.export_ops:
            enable_prop_name = 'enable_{}_export'.format(label.lower())
            enable_prop = getattr(preferences, enable_prop_name)
            if enable_prop:
                col.operator(operator.bl_idname, text=label, icon='EXPORT')


classes = (
    XRAY_PT_skls_animations,
    XRAY_PT_viewer,
    XRAY_PT_transforms,
    XRAY_PT_add,
    XRAY_PT_verify_tools,
    XRAY_PT_props_tools,
    XRAY_PT_batch_tools,
    XRAY_PT_custom_props,
    XRAY_PT_armature_tools,
    XRAY_PT_rig,
    XRAY_PT_update,
    XRAY_PT_import_operators,
    XRAY_PT_export_operators
)


def register():
    for clas in classes:
        bpy.utils.register_class(clas)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
