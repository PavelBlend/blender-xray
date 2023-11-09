# blender modules
import bpy

# addon modules
from .. import ui
from .. import menus
from .. import utils
from .. import text
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
    bl_label = 'Motions Browser'
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = ui.base.CATEGORY
    if utils.version.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout

        obj = context.active_object
        active = False
        if not obj is None:
            if obj.type == 'ARMATURE':
                active = True
            else:
                layout.label(
                    text=text.get_text(text.error.is_not_arm),
                    icon='ERROR'
                )
                return
        else:
            layout.label(
                text=text.get_text(text.error.no_active_obj),
                icon='ERROR'
            )
            return

        has_anims = len(obj.xray.motions_browser.animations)

        col = layout.column(align=True)
        col.active = active

        if not has_anims:
            row = col.row()
            row.label(text='Format:')
            row.prop(obj.xray.motions_browser, 'file_format', expand=True)

        col.operator(
            operator=ops.motions_browser.XRAY_OT_browse_motions_file.bl_idname,
            text='Open File',
            icon='FILE_FOLDER'
        )

        if has_anims:
            col.operator(
                ops.motions_browser.XRAY_OT_close_motions_file.bl_idname,
                icon='X'
            )
        col.template_list(
            listtype_name='XRAY_UL_motions_list_item',
            list_id='compact',
            dataptr=obj.xray.motions_browser,
            propname='animations',
            active_dataptr=obj.xray.motions_browser,
            active_propname='animations_index',
            rows=5
        )

        if not has_anims:
            return

        col = col.column()

        # select
        select_op_class = ops.motions_browser.XRAY_OT_motions_browser_select
        row = col.row(align=True)
        row.label(text='Select:')

        select_op = row.operator(select_op_class.bl_idname, text='All')
        select_op.mode = 'ALL'

        select_op = row.operator(select_op_class.bl_idname, text='None')
        select_op.mode = 'NONE'

        select_op = row.operator(select_op_class.bl_idname, text='Invert')
        select_op.mode = 'INVERT'

        # import
        import_op_class = ops.motions_browser.XRAY_OT_motions_browser_import
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
        viewer_props = scn.xray.viewer
        viewer_folder = viewer_props.folder

        if viewer_folder:
            col.operator(
                ops.viewer.XRAY_OT_viewer_close_folder.bl_idname,
                icon='X'
            )
            col.operator(
                ops.viewer.XRAY_OT_viewer_open_current_folder.bl_idname,
                text=viewer_folder,
                icon='FILE_FOLDER'
            )

            col_fmt = col.column(align=True)

            # formats
            col_fmt.label(text='Use Formats:')
            row = col_fmt.row(align=True)
            row.prop(
                viewer_props,
                'use_object',
                text='Object',
                toggle=True,
                translate=False
            )
            row.prop(viewer_props, 'use_ogf', toggle=True)
            row.prop(viewer_props, 'use_dm', toggle=True)
            row.prop(viewer_props, 'use_details', toggle=True)

            row = col.row(align=True)
            col_1 = row.column(align=True)
            col_2 = row.column(align=True)

            col_1.prop(viewer_props, 'import_motions')
            col_1.prop(viewer_props, 'sort_reverse')
            col_1.prop(viewer_props, 'ignore_ext')
            col_2.prop(viewer_props, 'show_size')
            col_2.prop(viewer_props, 'show_date')
            col_2.prop(viewer_props, 'group_by_ext')

            row = col.row(align=True)
            row.label(text='Sort:')
            row.prop(viewer_props, 'sort', expand=True)

            # folders count
            row = col.row()
            row.label(text='Folders:', icon='FILE_FOLDER')
            row = row.row()
            row.alignment = 'RIGHT'
            row.label(text=str(viewer_props.dirs_count))

            # files count
            row = col.row()
            row.label(text='Files:', icon='FILE')
            row = row.row()
            row.alignment = 'RIGHT'
            row.label(text=str(viewer_props.files_count))

            # files size
            row = col.row()
            row.label(text='Files Size:', icon='INFO')
            row = row.row()
            row.alignment = 'RIGHT'
            row.label(text=ops.viewer.get_size_label(viewer_props.files_size))

            col.operator(
                ops.viewer.XRAY_OT_viewer_preview_folder.bl_idname,
                icon='FILE_PARENT'
            )

            # files list
            col.template_list(
                listtype_name='XRAY_UL_viewer_list_item',
                list_id='compact',
                dataptr=viewer_props,
                propname='files',
                active_dataptr=viewer_props,
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
        col = layout.column(align=True)

        col.operator(
            ops.verify.XRAY_OT_verify_uv.bl_idname,
            icon='GROUP_UVS'
        )
        col.operator(ops.verify.XRAY_OT_check_invalid_faces.bl_idname)
        col.operator(ops.invalid_sg.XRAY_OT_check_invalid_sg_objs.bl_idname)


class XRAY_PT_omf_editor(ui.base.XRayPanel):
    bl_label = 'OMF Editor'
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
        col.operator(ops.omf_editor.XRAY_OT_merge_omf.bl_idname)


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
        if not context.active_object:
            lay.label(
                text=text.get_text(text.error.no_active_obj),
                icon='ERROR'
            )
            return
        data = context.active_object.xray
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
            ops.level_shaders.XRAY_OT_create_level_shader_nodes.bl_idname,
            icon='SCENE_DATA'
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
            ops.bone.XRAY_OT_resize_bones.bl_idname,
            icon='FULLSCREEN_ENTER'
        )

        has_arm = False
        active_obj = context.active_object
        if active_obj:
            if active_obj.type == 'ARMATURE':
                has_arm = True
            else:
                col = col.row().box().column(align=True)
                col.label(
                    text=text.get_text(text.error.is_not_arm),
                    icon='ERROR'
                )
        else:
            col = col.row().box().column(align=True)
            col.label(
                text=text.get_text(text.error.no_active_obj),
                icon='ERROR'
            )

        col.operator(
            ops.rig.connect_bones.XRAY_OT_create_connected_bones.bl_idname
        )
        col.operator(
            ops.armature.XRAY_OT_link_bones.bl_idname
        )
        col.operator(
            ops.armature.XRAY_OT_unlink_bones.bl_idname
        )

        col_danger = col.column(align=True)
        col_danger.alert = True
        col_danger.operator(
            ops.rig.remove_rig.XRAY_OT_remove_rig.bl_idname
        )

        if has_arm and context.mode != 'POSE':
            pose_mode = False
            pose_lay = col.row().box().column(align=True)
            pose_lay.label(
                text=text.get_text(text.error.not_pose_mode),
                icon='ERROR'
            )
        else:
            pose_mode = True
            pose_lay = col

        pose_lay.operator(
            ops.rig.create_ik.XRAY_OT_create_ik.bl_idname
        )

        limit_lay = pose_lay

        if has_arm and pose_mode:
            if not context.active_pose_bone:
                limit_lay = pose_lay.box().column(align=True)
                limit_lay.label(
                    text=text.get_text(text.error.no_active_bone),
                    icon='ERROR'
                )

        limit_lay.label(text='Set Joint Limits:')

        for limit in ('min', 'max'):
            row = limit_lay.row(align=True)
            for axis in ('X', 'Y', 'Z'):
                op_props = row.operator(
                    ops.joint_limits.XRAY_OT_set_joint_limits.bl_idname,
                    text='{0} {1}'.format(limit.title(), axis)
                )
                op_props.mode = '{0}_{1}'.format(limit.upper(), axis)

        row = limit_lay.row(align=True)
        for limit in ('min', 'max'):
            op_props = row.operator(
                ops.joint_limits.XRAY_OT_set_joint_limits.bl_idname,
                text='{0} XYZ'.format(limit.title())
            )
            op_props.mode = '{0}_XYZ'.format(limit.upper())

        row = limit_lay.row(align=True)
        for axis in ('X', 'Y', 'Z'):
            op_props = row.operator(
                ops.joint_limits.XRAY_OT_set_joint_limits.bl_idname,
                text='Min/Max {0}'.format(axis)
            )
            op_props.mode = 'MIN_MAX_{0}'.format(axis)

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

        obj = context.active_object

        if obj:
            if obj.type != 'ARMATURE':
                col.label(
                    text=text.get_text(text.error.is_not_arm),
                    icon='ERROR'
                )
                return

        else:
            col.label(
                text=text.get_text(text.error.no_active_obj),
                icon='ERROR'
            )
            return

        if context.mode != 'POSE':
            col.label(
                text=text.get_text(text.error.not_pose_mode),
                icon='ERROR'
            )
            return

        ik_fk_bones = []
        bones = obj.pose.bones

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


def get_operator_key(op_id):
    wm = bpy.context.window_manager
    if utils.version.IS_293:
        config = 'Blender user'
    elif utils.version.IS_28:
        config = 'blender user'
    else:
        config = 'Blender User'
    view_3d_keys = wm.keyconfigs[config].keymaps['3D View']
    key = view_3d_keys.keymap_items.get(op_id)

    if not key:
        return ''

    if key.shift:
        shift = 'Shift '
    else:
        shift = ''

    if key.ctrl:
        ctrl = 'Ctrl '
    else:
        ctrl = ''

    if key.alt:
        alt = 'Alt '
    else:
        alt = ''

    return shift + ctrl + alt + key.type


class ImportExportBasePanel(ui.base.XRayPanel):
    bl_category = ui.base.CATEGORY
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}

    if utils.version.IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        ops = getattr(menus, '{}_ops'.format(cls.panel_type))
        enabled_operators = menus.get_enabled_operators(
            ops,
            cls.panel_type
        )
        return bool(enabled_operators)

    def draw(self, context):
        pref = utils.version.get_preferences()

        if pref.paths_mode == 'ADVANCED':
            col = self.layout.column(align=True)
            col.label(text='Paths Config:')
            col.prop_search(
                pref,
                'used_config',
                pref,
                'paths_configs',
                text=''
            )

        col = self.layout.column(align=True)
        ops = getattr(menus, '{}_ops'.format(self.panel_type))

        for operator, label in ops:
            enable_prop_name = 'enable_{}_{}'.format(
                label.lower(),
                self.panel_type
            )
            enable_prop = getattr(pref, enable_prop_name)

            if enable_prop:
                split = utils.version.layout_split(col, 0.5, align=True)

                # draw button
                op = split.operator(
                    operator.bl_idname,
                    text=label,
                    icon=self.panel_type.upper(),
                    translate=False
                )
                op.processed = True

                # draw keymap
                key = get_operator_key(operator.bl_idname)
                row_key = split.row(align=True)
                row_key.alignment = 'RIGHT'
                row_key.label(text=key)


class XRAY_PT_import_operators(ImportExportBasePanel):
    bl_label = 'Import'
    panel_type = 'import'


class XRAY_PT_export_operators(ImportExportBasePanel):
    bl_label = 'Export'
    panel_type = 'export'


classes = (
    XRAY_PT_skls_animations,
    XRAY_PT_viewer,
    XRAY_PT_omf_editor,
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
