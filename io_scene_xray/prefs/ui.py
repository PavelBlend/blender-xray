# blender modules
import rna_keymap_ui

# addon modules
from . import ops
from . import props
from . import preset
from .. import version_utils
from .. import hotkeys
from .. import utils
from .. import draw_utils


path_props_names = {
    'fs_ltx_file': 'FS Ltx File',
    'gamedata_folder': 'Gamedata Folder',
    'textures_folder': 'Textures Folder',
    'meshes_folder': 'Meshes Folder',
    'gamemtl_file': 'Game Materials File',
    'eshader_file': 'Engine Shaders File',
    'cshader_file': 'Compile Shaders File',
    'objects_folder': 'Objects Folder'
}


def get_split(layout):
    return version_utils.layout_split(layout, 0.3)


def prop_bool(layout, data, prop):
    layout.prop(data, prop)


def draw_path_prop(prefs, prop):
    layout = prefs.layout
    split = get_split(layout)
    split.label(text=path_props_names[prop] + ':')
    auto_prop = props.build_auto_id(prop)
    if getattr(prefs, auto_prop) and not getattr(prefs, prop):
        row = split.row(align=True)
        row_prop = row.row(align=True)
        row_prop.enabled = False
        row_prop.prop(prefs, auto_prop, text='')
        operator = row.operator(
            ops.XRAY_OT_explicit_path.bl_idname,
            icon='MODIFIER',
            text=''
        )
        operator.path = prop
    else:
        split.prop(prefs, prop, text='')


def draw_prop_name(prefs, name, param):
    layout = prefs.layout
    row = layout.row()
    row.label(text=name)
    row.prop(prefs.custom_props, param, text='')


def draw_presets(prefs):
    layout = prefs.layout
    row = layout.row(align=True)
    row.menu(
        preset.XRAY_MT_prefs_presets.__name__,
        text=preset.XRAY_MT_prefs_presets.bl_label
    )
    row.operator(
        preset.XRAY_OT_add_prefs_preset.bl_idname,
        text='',
        icon=version_utils.get_icon('ZOOMIN')
    )
    row.operator(
        preset.XRAY_OT_add_prefs_preset.bl_idname,
        text='',
        icon=version_utils.get_icon('ZOOMOUT')
    ).remove_active = True


def draw_paths(prefs):
    layout = prefs.layout
    split = get_split(layout)
    split.label(text=path_props_names['fs_ltx_file'] + ':')
    split.prop(prefs, 'fs_ltx_file', text='')
    draw_path_prop(prefs, 'gamedata_folder')
    draw_path_prop(prefs, 'textures_folder')
    draw_path_prop(prefs, 'meshes_folder')
    draw_path_prop(prefs, 'gamemtl_file')
    draw_path_prop(prefs, 'eshader_file')
    draw_path_prop(prefs, 'cshader_file')
    draw_path_prop(prefs, 'objects_folder')


def draw_defaults(prefs):
    layout = prefs.layout
    layout.row().prop(prefs, 'defaults_category', expand=True)
    if prefs.defaults_category == 'OBJECT':
        # import object props
        box = layout.box()
        box.label(text='Import:')
        draw_utils.draw_fmt_ver_prop(box, prefs, 'sdk_version', lay_type='ROW')
        box.prop(prefs, 'object_motions_import')
        box.prop(prefs, 'object_mesh_split_by_mat')
        # export object props
        box = layout.box()
        box.label(text='Export:')
        draw_utils.draw_fmt_ver_prop(box, prefs, 'export_object_sdk_version', lay_type='ROW')
        row = box.row()
        row.label(text='Smoothing:')
        row.prop(prefs, 'smoothing_out_of', expand=True)
        box.prop(prefs, 'object_motions_export')
        box.prop(prefs, 'object_texture_names_from_path')
        box.prop(prefs, 'export_object_use_export_paths')
    elif prefs.defaults_category == 'ANM':
        # import
        box = layout.box()
        box.label(text='Import:')
        box.prop(prefs, 'anm_create_camera')
        # export
        box = layout.box()
        box.label(text='Export:')
        draw_utils.draw_fmt_ver_prop(box, prefs, 'anm_format_version', lay_type='ROW')
    elif prefs.defaults_category == 'SKLS':
        box = layout.box()
        box.label(text='Import:')
        box.prop(prefs, 'add_actions_to_motion_list')
    elif prefs.defaults_category == 'BONES':
        box = layout.box()
        # import
        box.label(text='Import:')
        box.prop(prefs, 'bones_import_bone_parts')
        box.prop(prefs, 'bones_import_bone_properties')
        # export
        box = layout.box()
        box.label(text='Export:')
        box.prop(prefs, 'bones_export_bone_parts')
        box.prop(prefs, 'bones_export_bone_properties')
    elif prefs.defaults_category == 'DETAILS':
        box = layout.box()
        # import
        box.label(text='Import:')
        box.prop(prefs, 'details_models_in_a_row')
        box.prop(prefs, 'load_slots')
        draw_utils.draw_fmt_ver_prop(box, prefs, 'details_format', lay_type='ROW')
        # export
        box = layout.box()
        box.label(text='Export:')
        box.prop(prefs, 'details_texture_names_from_path')
        draw_utils.draw_fmt_ver_prop(box, prefs, 'format_version', lay_type='ROW')
    elif prefs.defaults_category == 'DM':
        box = layout.box()
        box.label(text='Export:')
        box.prop(prefs, 'dm_texture_names_from_path')
    elif prefs.defaults_category == 'OGF':
        # import
        box = layout.box()
        box.label(text='Import:')
        box.prop(prefs, 'ogf_import_motions')
        # export
        box = layout.box()
        box.label(text='Export:')
        box.prop(prefs, 'ogf_texture_names_from_path')
        box.prop(prefs, 'ogf_export_motions')
    elif prefs.defaults_category == 'OMF':
        box = layout.box()
        # import
        box.label(text='Import:')
        box.prop(prefs, 'omf_import_motions')
        box.prop(prefs, 'import_bone_parts')
        box.prop(prefs, 'omf_add_actions_to_motion_list')
        # export
        box = layout.box()
        box.label(text='Export:')
        box.prop(prefs, 'omf_motions_export')
        box.prop(prefs, 'omf_export_bone_parts')
        box.prop(prefs, 'omf_high_quality')
        row = box.row()
        row.label(text='Export Mode:')
        row.prop(prefs, 'omf_export_mode', expand=True)
    elif prefs.defaults_category == 'SCENE':
        box = layout.box()
        box.label(text='Import:')
        draw_utils.draw_fmt_ver_prop(box, prefs, 'scene_selection_sdk_version', lay_type='ROW')
        box.prop(prefs, 'scene_selection_mesh_split_by_mat')
    elif prefs.defaults_category == 'PART':
        box = layout.box()
        box.label(text='Import:')
        draw_utils.draw_fmt_ver_prop(box, prefs, 'part_sdk_version', lay_type='ROW')
        box.prop(prefs, 'part_mesh_split_by_mat')


def draw_formats_enable_disable(prefs):
    layout = prefs.layout
    row = layout.row(align=True)
    # import operators
    column_import = row.column(align=True)
    column_import.label(text='Import Formats:')
    column_import.prop(prefs, 'enable_object_import', text='*.object')
    column_import.prop(prefs, 'enable_skls_import', text='*.skl *.skls')
    column_import.prop(prefs, 'enable_ogf_import', text='*.ogf')
    column_import.prop(prefs, 'enable_omf_import', text='*.omf')
    column_import.prop(prefs, 'enable_anm_import', text='*.anm')
    column_import.prop(prefs, 'enable_bones_import', text='*.bones')
    column_import.prop(prefs, 'enable_dm_import', text='*.dm')
    column_import.prop(prefs, 'enable_details_import', text='*.details')
    column_import.prop(prefs, 'enable_level_import', text='*.level')
    column_import.prop(prefs, 'enable_game_level_import', text='level')
    column_import.prop(prefs, 'enable_part_import', text='*.part')
    column_import.prop(prefs, 'enable_err_import', text='*.err')
    # export operators
    column_export = row.column(align=True)
    column_export.label(text='Export Formats:')
    column_export.prop(prefs, 'enable_object_export', text='*.object')
    skls_row = column_export.row(align=True)
    skls_row.alignment = 'LEFT'
    skls_row.prop(prefs, 'enable_skl_export', text='*.skl')
    skls_row.prop(prefs, 'enable_skls_export', text='*.skls')
    column_export.prop(prefs, 'enable_ogf_export', text='*.ogf')
    column_export.prop(prefs, 'enable_omf_export', text='*.omf')
    column_export.prop(prefs, 'enable_anm_export', text='*.anm')
    column_export.prop(prefs, 'enable_bones_export', text='*.bones')
    column_export.prop(prefs, 'enable_dm_export', text='*.dm')
    column_export.prop(prefs, 'enable_details_export', text='*.details')
    column_export.prop(prefs, 'enable_level_export', text='*.level')
    column_export.prop(prefs, 'enable_game_level_export', text='level')


def draw_keymaps(context, prefs):
    layout = prefs.layout
    win_manager = context.window_manager
    keyconfig = win_manager.keyconfigs.user
    keymaps = keyconfig.keymaps.get('3D View')
    if keymaps:
        keymap_items = keymaps.keymap_items
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
                    props.XRAY_OT_add_keymap.bl_idname,
                    text='Add'
                )
                change_keymap_op.operator = operator.bl_idname


def draw_custom_props(prefs):
    layout = prefs.layout
    layout.row().prop(prefs.custom_props, 'category', expand=True)
    # object
    if prefs.custom_props.category == 'OBJECT':
        draw_prop_name(prefs, 'Flags:', 'object_flags')
        draw_prop_name(prefs, 'Userdata:', 'object_userdata')
        draw_prop_name(prefs, 'LOD Reference:', 'object_lod_reference')
        draw_prop_name(prefs, 'Owner Name:', 'object_owner_name')
        draw_prop_name(prefs, 'Creation Time:', 'object_creation_time')
        draw_prop_name(prefs, 'Modif Name:', 'object_modif_name')
        draw_prop_name(prefs, 'Modified Time:', 'object_modified_time')
        draw_prop_name(prefs, 'Motion References:', 'object_motion_references')
    # mesh
    elif prefs.custom_props.category == 'MESH':
        draw_prop_name(prefs, 'Flags:', 'mesh_flags')
    # material
    elif prefs.custom_props.category == 'MATERIAL':
        draw_prop_name(prefs, 'Two Sided:', 'material_two_sided')
        draw_prop_name(prefs, 'Shader:', 'material_shader')
        draw_prop_name(prefs, 'Compile:', 'material_compile')
        draw_prop_name(prefs, 'Game Mtl:', 'material_game_mtl')
    # bone
    elif prefs.custom_props.category == 'BONE':
        layout.row().prop(prefs.custom_props, 'bone_category', expand=True)
        if prefs.custom_props.bone_category == 'MAIN':
            draw_prop_name(prefs, 'Game Mtl:', 'bone_game_mtl')
            draw_prop_name(prefs, 'Length:', 'bone_length')
            # mass
            draw_prop_name(prefs, 'Mass:', 'bone_mass')
            draw_prop_name(prefs, 'Center of Mass:', 'bone_center_of_mass')
            # other
            draw_prop_name(prefs, 'Breakable Force:', 'bone_breakable_force')
            draw_prop_name(prefs, 'Breakable Torque:', 'bone_breakable_torque')
            draw_prop_name(prefs, 'Friction:', 'bone_friction')
        elif prefs.custom_props.bone_category == 'SHAPE':
            draw_prop_name(prefs, 'Shape Flags:', 'bone_shape_flags')
            draw_prop_name(prefs, 'Shape Type:', 'bone_shape_type')
            # box shape
            draw_prop_name(prefs, 'Box Shape Rotation:', 'bone_box_shape_rotation')
            draw_prop_name(prefs, 'Box Shape Translate:', 'bone_box_shape_translate')
            draw_prop_name(prefs, 'Box Shape Half Size:', 'bone_box_shape_half_size')
            # sphere shape
            draw_prop_name(prefs, 'Sphere Shape Position:', 'bone_sphere_shape_position')
            draw_prop_name(prefs, 'Sphere Shape Radius:', 'bone_sphere_shape_radius')
            # cylinder shape
            draw_prop_name(prefs, 'Cylinder Shape Position:', 'bone_cylinder_shape_position')
            draw_prop_name(prefs, 'Cylinder Shape Direction:', 'bone_cylinder_shape_direction')
            draw_prop_name(prefs, 'Cylinder Shape Hight:', 'bone_cylinder_shape_hight')
            draw_prop_name(prefs, 'Cylinder Shape Radius:', 'bone_cylinder_shape_radius')
        elif prefs.custom_props.bone_category == 'IK':
            # ik
            draw_prop_name(prefs, 'IK Joint Type:', 'bone_ik_joint_type')
            draw_prop_name(prefs, 'IK Flags:', 'bone_ik_flags')
            # limit
            draw_prop_name(prefs, 'Limit X Min:', 'bone_limit_x_min')
            draw_prop_name(prefs, 'Limit X Max:', 'bone_limit_x_max')
            draw_prop_name(prefs, 'Limit Y Min:', 'bone_limit_y_min')
            draw_prop_name(prefs, 'Limit Y Max:', 'bone_limit_y_max')
            draw_prop_name(prefs, 'Limit Z Min:', 'bone_limit_z_min')
            draw_prop_name(prefs, 'Limit Z Max:', 'bone_limit_z_max')
            # spring
            draw_prop_name(prefs, 'Limit X Spring:', 'bone_limit_x_spring')
            draw_prop_name(prefs, 'Limit Y Spring:', 'bone_limit_y_spring')
            draw_prop_name(prefs, 'Limit Z Spring:', 'bone_limit_z_spring')
            # damping
            draw_prop_name(prefs, 'Limit X Damping:', 'bone_limit_x_damping')
            draw_prop_name(prefs, 'Limit Y Damping:', 'bone_limit_y_damping')
            draw_prop_name(prefs, 'Limit Z Damping:', 'bone_limit_z_damping')
            # spring and damping
            draw_prop_name(prefs, 'Spring:', 'bone_spring')
            draw_prop_name(prefs, 'Damping:', 'bone_damping')
    # action
    elif prefs.custom_props.category == 'ACTION':
        draw_prop_name(prefs, 'FPS:', 'action_fps')
        draw_prop_name(prefs, 'Speed:', 'action_speed')
        draw_prop_name(prefs, 'Accrue:', 'action_accrue')
        draw_prop_name(prefs, 'Falloff:', 'action_falloff')
        draw_prop_name(prefs, 'Bone Part:', 'action_bone_part')
        draw_prop_name(prefs, 'Flags:', 'action_flags')
        draw_prop_name(prefs, 'Power:', 'action_power')


def draw_others(prefs):
    layout = prefs.layout
    split = version_utils.layout_split(layout, 0.4)
    split.label(text='Custom Owner Name:')
    split.prop(prefs, 'custom_owner_name', text='')
    prop_bool(layout, prefs, 'compact_menus')
    box = layout.box()
    box.label(text='Bone Shape Colors:')
    row = box.row()
    row.prop(prefs, 'gl_active_shape_color')
    row = box.row()
    row.prop(prefs, 'gl_select_shape_color')
    row = box.row()
    row.prop(prefs, 'gl_shape_color')
    row = box.row()
    row.prop(prefs, 'gl_object_mode_shape_color')
