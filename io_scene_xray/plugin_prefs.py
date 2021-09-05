# blender modules
import bpy
import rna_keymap_ui
import bl_operators

# addon modules
from . import prefs
from . import hotkeys
from . import version_utils


path_props_names = {
    'fs_ltx_file': 'FS Ltx File',
    'gamedata_folder': 'Gamedata Folder',
    'textures_folder': 'Textures Folder',
    'gamemtl_file': 'Game Materials File',
    'eshader_file': 'Engine Shaders File',
    'cshader_file': 'Compile Shaders File',
    'objects_folder': 'Objects Folder'
}


class XRAY_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = 'io_scene_xray'

    if not version_utils.IS_28:
        for prop_name, prop_value in prefs.props.plugin_preferences_props.items():
            exec('{0} = prefs.props.plugin_preferences_props.get("{0}")'.format(prop_name))

    def get_split(self, layout):
        return version_utils.layout_split(layout, 0.3)

    def draw_path_prop(self, prop):
        layout = self.layout
        split = self.get_split(layout)
        split.label(text=path_props_names[prop] + ':')
        auto_prop = prefs.props.build_auto_id(prop)
        if getattr(self, auto_prop) and not getattr(self, prop):
            row = split.row(align=True)
            row_prop = row.row(align=True)
            row_prop.enabled = False
            row_prop.prop(self, auto_prop, text='')
            operator = row.operator(
                prefs.ops.XRAY_OT_explicit_path.bl_idname, icon='MODIFIER', text=''
            )
            operator.path = prop
        else:
            split.prop(self, prop, text='')

    def draw(self, context):

        def prop_bool(layout, data, prop):
            layout.prop(data, prop)

        layout = self.layout

        row = layout.row(align=True)
        row.menu(XRAY_MT_prefs_presets.__name__, text=XRAY_MT_prefs_presets.bl_label)
        row.operator(XRAY_OT_add_prefs_preset.bl_idname, text='', icon=version_utils.get_icon('ZOOMIN'))
        row.operator(XRAY_OT_add_prefs_preset.bl_idname, text='', icon=version_utils.get_icon('ZOOMOUT')).remove_active = True

        layout.row().prop(self, 'category', expand=True)

        if self.category == 'PATHS':
            split = self.get_split(layout)
            split.label(text=path_props_names['fs_ltx_file'] + ':')
            split.prop(self, 'fs_ltx_file', text='')
            self.draw_path_prop('gamedata_folder')
            self.draw_path_prop('textures_folder')
            self.draw_path_prop('gamemtl_file')
            self.draw_path_prop('eshader_file')
            self.draw_path_prop('cshader_file')
            self.draw_path_prop('objects_folder')
        elif self.category == 'DEFAULTS':
            layout.row().prop(self, 'defaults_category', expand=True)
            if self.defaults_category == 'OBJECT':
                # import object props
                box = layout.box()
                box.label(text='Import:')
                row = box.row()
                row.label(text='SDK Version:')
                row.prop(self, 'sdk_version', expand=True)
                box.prop(self, 'object_motions_import')
                box.prop(self, 'use_motion_prefix_name')
                box.prop(self, 'object_mesh_split_by_mat')
                # export object props
                box = layout.box()
                box.label(text='Export:')
                row = box.row()
                row.label(text='SDK Version:')
                row.prop(self, 'export_object_sdk_version', expand=True)
                row = box.row()
                row.label(text='Smoothing Out of:')
                row.prop(self, 'smoothing_out_of', expand=True)
                box.prop(self, 'object_motions_export')
                box.prop(self, 'object_texture_names_from_path')
                box.prop(self, 'export_object_use_export_paths')
            elif self.defaults_category == 'ANM':
                box = layout.box()
                box.label(text='Import:')
                box.prop(self, 'anm_create_camera')
            elif self.defaults_category == 'SKLS':
                box = layout.box()
                box.label(text='Import:')
                box.prop(self, 'skls_use_motion_prefix_name')
                box.prop(self, 'add_actions_to_motion_list')
            elif self.defaults_category == 'BONES':
                box = layout.box()
                # import
                box.label(text='Import:')
                box.prop(self, 'bones_import_bone_parts')
                box.prop(self, 'bones_import_bone_properties')
                # export
                box = layout.box()
                box.label(text='Export:')
                box.prop(self, 'bones_export_bone_parts')
                box.prop(self, 'bones_export_bone_properties')
            elif self.defaults_category == 'DETAILS':
                box = layout.box()
                # import
                box.label(text='Import:')
                box.prop(self, 'details_models_in_a_row')
                box.prop(self, 'load_slots')
                row = box.row()
                row.label(text='Details Format:')
                row.prop(self, 'details_format', expand=True)
                # export
                box = layout.box()
                box.label(text='Export:')
                box.prop(self, 'details_texture_names_from_path')
                row = box.row()
                row.label(text='Details Format:')
                row.prop(self, 'format_version', expand=True)
            elif self.defaults_category == 'DM':
                box = layout.box()
                box.label(text='Export:')
                box.prop(self, 'dm_texture_names_from_path')
            elif self.defaults_category == 'OGF':
                # import
                box = layout.box()
                box.label(text='Import:')
                box.prop(self, 'ogf_import_motions')
                # export
                box = layout.box()
                box.label(text='Export:')
                box.prop(self, 'ogf_texture_names_from_path')
            elif self.defaults_category == 'OMF':
                box = layout.box()
                # import
                box.label(text='Import:')
                box.prop(self, 'omf_import_motions')
                box.prop(self, 'import_bone_parts')
                box.prop(self, 'omf_add_actions_to_motion_list')
                # export
                box = layout.box()
                box.label(text='Export:')
                box.prop(self, 'omf_motions_export')
                box.prop(self, 'omf_export_bone_parts')
                row = box.row()
                row.label(text='Export Mode:')
                row.prop(self, 'omf_export_mode', expand=True)
            elif self.defaults_category == 'SCENE':
                box = layout.box()
                box.label(text='Import:')
                row = box.row()
                row.label(text='SDK Version:')
                row.prop(self, 'scene_selection_sdk_version', expand=True)
                box.prop(self, 'scene_selection_mesh_split_by_mat')

        elif self.category == 'PLUGINS':
            row = layout.row()

            column_1 = row.column()
            column_2 = row.column()

            column_1.label(text='Import Plugins:')
            column_1.prop(self, 'enable_object_import', text='*.object')
            column_1.prop(self, 'enable_anm_import', text='*.anm')
            column_1.prop(self, 'enable_dm_import', text='*.dm')
            column_1.prop(self, 'enable_details_import', text='*.details')
            column_1.prop(self, 'enable_skls_import', text='*.skls')
            column_1.prop(self, 'enable_bones_import', text='*.bones')
            column_1.prop(self, 'enable_level_import', text='*.level')
            column_1.prop(self, 'enable_omf_import', text='*.omf')
            column_1.prop(self, 'enable_game_level_import', text='level')
            column_1.prop(self, 'enable_ogf_import', text='*.ogf')
            column_1.prop(self, 'enable_err_import', text='*.err')

            column_2.label(text='Export Plugins:')
            column_2.prop(self, 'enable_object_export', text='*.object')
            column_2.prop(self, 'enable_anm_export', text='*.anm')
            column_2.prop(self, 'enable_dm_export', text='*.dm')
            column_2.prop(self, 'enable_details_export', text='*.details')
            column_2.prop(self, 'enable_skls_export', text='*.skls')
            column_2.prop(self, 'enable_bones_export', text='*.bones')
            column_2.prop(self, 'enable_level_export', text='*.level')
            column_2.prop(self, 'enable_omf_export', text='*.omf')
            column_2.prop(self, 'enable_game_level_export', text='level')
            column_2.prop(self, 'enable_ogf_export', text='*.ogf')

        elif self.category == 'KEYMAP':
            win_manager = context.window_manager
            keyconfig = win_manager.keyconfigs.user
            keymaps = keyconfig.keymaps.get('3D View')
            if keymaps:
                keymap_items = keymaps.keymap_items
                operators = (
                    'xray_import.object',
                    'xray_export.object'
                )
                for operator, _, _, _, _ in hotkeys.keymap_items_list:
                    row = layout.row(align=True)
                    keymap = keymap_items.get(operator.bl_idname)
                    if keymap:
                        row.context_pointer_set('keymap', keymaps)
                        rna_keymap_ui.draw_kmi(
                            ["ADDON", "USER", "DEFAULT"],
                            keyconfig, keymaps, keymap, row, 0
                        )
                    else:
                        row.label(text=operator.bl_label)
                        change_keymap_op = row.operator(
                            prefs.props.XRAY_OT_add_keymap.bl_idname,
                            text='Add'
                        )
                        change_keymap_op.operator = operator.bl_idname

        # custom properties settings
        elif self.category == 'CUSTOM_PROPS':
            layout.row().prop(self.custom_props, 'category', expand=True)
            def draw_prop_name(name, param):
                row = layout.row()
                row.label(text=name)
                row.prop(self.custom_props, param, text='')
            # object
            if self.custom_props.category == 'OBJECT':
                draw_prop_name('Flags:', 'object_flags')
                draw_prop_name('Userdata:', 'object_userdata')
                draw_prop_name('LOD Reference:', 'object_lod_reference')
                draw_prop_name('Owner Name:', 'object_owner_name')
                draw_prop_name('Creation Time:', 'object_creation_time')
                draw_prop_name('Modif Name:', 'object_modif_name')
                draw_prop_name('Modified Time:', 'object_modified_time')
                draw_prop_name('Motion References:', 'object_motion_references')
            # mesh
            elif self.custom_props.category == 'MESH':
                draw_prop_name('Flags:', 'mesh_flags')
            # material
            elif self.custom_props.category == 'MATERIAL':
                draw_prop_name('Two Sided:', 'material_two_sided')
                draw_prop_name('Shader:', 'material_shader')
                draw_prop_name('Compile:', 'material_compile')
                draw_prop_name('Game Mtl:', 'material_game_mtl')
            # bone
            elif self.custom_props.category == 'BONE':
                layout.row().prop(self.custom_props, 'bone_category', expand=True)
                if self.custom_props.bone_category == 'MAIN':
                    draw_prop_name('Game Mtl:', 'bone_game_mtl')
                    draw_prop_name('Length:', 'bone_length')
                    # mass
                    draw_prop_name('Mass:', 'bone_mass')
                    draw_prop_name('Center of Mass:', 'bone_center_of_mass')
                    # other
                    draw_prop_name('Breakable Force:', 'bone_breakable_force')
                    draw_prop_name('Breakable Torque:', 'bone_breakable_torque')
                    draw_prop_name('Friction:', 'bone_friction')
                elif self.custom_props.bone_category == 'SHAPE':
                    draw_prop_name('Shape Flags:', 'bone_shape_flags')
                    draw_prop_name('Shape Type:', 'bone_shape_type')
                    # box shape
                    draw_prop_name('Box Shape Rotation:', 'bone_box_shape_rotation')
                    draw_prop_name('Box Shape Translate:', 'bone_box_shape_translate')
                    draw_prop_name('Box Shape Half Size:', 'bone_box_shape_half_size')
                    # sphere shape
                    draw_prop_name('Sphere Shape Position:', 'bone_sphere_shape_position')
                    draw_prop_name('Sphere Shape Radius:', 'bone_sphere_shape_radius')
                    # cylinder shape
                    draw_prop_name('Cylinder Shape Position:', 'bone_cylinder_shape_position')
                    draw_prop_name('Cylinder Shape Direction:', 'bone_cylinder_shape_direction')
                    draw_prop_name('Cylinder Shape Hight:', 'bone_cylinder_shape_hight')
                    draw_prop_name('Cylinder Shape Radius:', 'bone_cylinder_shape_radius')
                elif self.custom_props.bone_category == 'IK':
                    # ik
                    draw_prop_name('IK Joint Type:', 'bone_ik_joint_type')
                    draw_prop_name('IK Flags:', 'bone_ik_flags')
                    # limit
                    draw_prop_name('Limit X Min:', 'bone_limit_x_min')
                    draw_prop_name('Limit X Max:', 'bone_limit_x_max')
                    draw_prop_name('Limit Y Min:', 'bone_limit_y_min')
                    draw_prop_name('Limit Y Max:', 'bone_limit_y_max')
                    draw_prop_name('Limit Z Min:', 'bone_limit_z_min')
                    draw_prop_name('Limit Z Max:', 'bone_limit_z_max')
                    # spring
                    draw_prop_name('Limit X Spring:', 'bone_limit_x_spring')
                    draw_prop_name('Limit Y Spring:', 'bone_limit_y_spring')
                    draw_prop_name('Limit Z Spring:', 'bone_limit_z_spring')
                    # damping
                    draw_prop_name('Limit X Damping:', 'bone_limit_x_damping')
                    draw_prop_name('Limit Y Damping:', 'bone_limit_y_damping')
                    draw_prop_name('Limit Z Damping:', 'bone_limit_z_damping')
                    # spring and damping
                    draw_prop_name('Spring:', 'bone_spring')
                    draw_prop_name('Damping:', 'bone_damping')
            # action
            elif self.custom_props.category == 'ACTION':
                draw_prop_name('FPS:', 'action_fps')
                draw_prop_name('Speed:', 'action_speed')
                draw_prop_name('Accrue:', 'action_accrue')
                draw_prop_name('Falloff:', 'action_falloff')
                draw_prop_name('Bone Part:', 'action_bone_part')
                draw_prop_name('Flags:', 'action_flags')
                draw_prop_name('Power:', 'action_power')

        elif self.category == 'OTHERS':
            split = version_utils.layout_split(layout, 0.4)
            split.label(text='Custom Owner Name:')
            split.prop(self, 'custom_owner_name', text='')
            prop_bool(layout, self, 'expert_mode')
            prop_bool(layout, self, 'compact_menus')
            prop_bool(layout, self, 'developer_mode')
            row = layout.row()
            row.prop(self, 'gl_shape_color')
            row = layout.row()
            row.prop(self, 'gl_select_shape_color')
            row = layout.row()
            row.prop(self, 'gl_active_shape_color')
            row = layout.row()
            row.prop(self, 'gl_object_mode_shape_color')

        split = version_utils.layout_split(layout, 0.6)
        split.label(text='')
        split.operator(
            prefs.ops.XRAY_OT_reset_prefs_settings.bl_idname, icon='CANCEL'
        )


class XRAY_MT_prefs_presets(bpy.types.Menu):
    bl_label = 'Settings Presets'
    preset_subdir = 'io_scene_xray/preferences'
    preset_operator = 'script.execute_preset'
    draw = bpy.types.Menu.draw_preset


class XRAY_OT_add_prefs_preset(bl_operators.presets.AddPresetBase, bpy.types.Operator):
    bl_idname = 'xray.prefs_preset_add'
    bl_label = 'Add XRay Preferences Preset'
    preset_menu = 'XRAY_MT_prefs_presets'

    preset_defines = [
        'prefs = bpy.context.preferences.addons["io_scene_xray"].preferences'
    ]
    preset_values = []
    for prop_key in prefs.props.plugin_preferences_props.keys():
        preset_values.append('prefs.{}'.format(prop_key))
    for auto_prop_key in prefs.props.__AUTO_PROPS__:
        preset_values.append('prefs.{}'.format(auto_prop_key))
        preset_values.append('prefs.{}_auto'.format(auto_prop_key))
    preset_subdir = 'io_scene_xray/preferences'


classes = (
    XRAY_MT_prefs_presets,
    XRAY_OT_add_prefs_preset,
    XRAY_addon_preferences
)


def register():
    version_utils.assign_props([
        (prefs.props.plugin_preferences_props, XRAY_addon_preferences),
    ])
    prefs.register()
    for clas in classes:
        bpy.utils.register_class(clas)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
    prefs.unregister()
