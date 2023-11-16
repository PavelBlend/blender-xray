# general
error_title = 'Error'
no_sel_files = 'No files selected!'
fatal_import_error = 'Import error. File not imported'
mat_no_img = 'Material has no image'
mat_many_img = 'Material has more the one image'
mat_many_tex = 'Material has more than one texture'
no_tex = 'Material has no texture'
no_uv = 'Mesh-object has no UV-map'
mat_not_use_nodes = 'Material does not use nodes'
obj_empty_mat = 'Object use empty material slot'
obj_no_mat = 'Object has no material'
many_mat = 'Mesh-object has more than one material'
file_another_prog = 'Unable to write file. The file is open in another program'
no_active_obj = 'No active object!'
no_selected_obj = 'No selected objects!'
no_blend_obj = 'Current blend-file has no objects'
is_not_arm = 'Active object is not armature!'
file_not_found = 'File not found'
file_folder_not_found = 'File or folder not found'
ltx_invalid_syntax = 'LTX file syntax error'
has_no_main_chunk = 'File has no main data block'
arm_non_uniform_scale = 'Object has an non-uniform scale'
not_pose_mode = 'Pose mode not activated!'
no_active_bone = 'No active bone!'

# anm export
anm_no_keys = 'Action has keys not for all channels'

# anm import
anm_unsupport_ver = 'File has unsupported format version'

# details convert
details_light_1569 = 'Object has incorrect light format: "Builds 1096-1558". Must be "Builds 1569-CoP"'
details_light_1096 = 'Object has incorrect light format: "Builds 1569-CoP". Must be "Builds 1096-1558"'
details_slots_size = '"Slots Base Object" size not equal "Slots Top Object" size'
details_poly_count = 'Slots object has an incorrect number of polygons'
details_img_size = 'Image has incorrect size'

# details import
details_bad_header = 'Bad DETAILS file. HEADER chunk size not equal 24'
details_unsupport_ver = 'Unsupported DETAILS format version'
details_no_header = 'Bad DETAILS file. Cannot find HEADER chunk'
details_no_meshes = 'Bad DETAILS file. Cannot find MESHES chunk'
details_no_slots = 'Bad DETAILS file. Cannot find SLOTS chunk'

# details utility
details_has_no_img = 'Level details object has no image property'
details_has_no_obj = 'Level details object has no object property'
details_cannot_find_img = 'Cannot find image'
details_cannot_find_obj = 'Cannot find object'
details_wrong_type = 'Object has wrong type'

# details write
details_file_duplicates = 'Duplicate paths found'
details_no_children = 'Details meshes object has no children'
details_many_children = 'Meshes object has too many children'
details_not_mesh = 'Meshes object child is not a mesh'
details_bad_detail_index = 'Object has incorrect "Detail Index"'
details_no_model_index = 'Not detail model with index'
details_duplicate_model = 'Duplicated index in detail models'

# dm create
dm_bad_indices = 'Bad DM triangle indices'

# dm export
dm_many_verts = 'Mesh-object has too many vertices'

# dm validate
dm_tex_type = 'Texture has an incorrect type'

# level import
level_unsupport_ver = 'Unsupported game level version'
level_has_no_geom = 'File *.geom not found'

# level cform import
cform_unsupport_ver = 'Unsupported level cform version'

# level export
level_no_lmap = 'Cannot find light map image'
level_has_children = 'Normal/Progressive object must not have children'
level_lmap_no_dds = 'Incorrect light map format (must be *.dds)'
level_sector_has_no_cform = 'Sector has no cform-object'
level_no_lights = 'Level-object has no light-objects'
level_no_sectors = 'Level-object has no sector-objects'

# level export visual
level_visual_is_not_mesh = 'Visual-object is not a mesh'
level_visual_no_faces = 'Visual mesh-object has no faces'
level_visual_no_mat = 'Visual-object has no material'
level_visual_empty_mat = 'Visual-object has empty material slot'
level_visual_many_mats = 'Visual-object has more than one material'
level_visual_no_uv = 'Visual-object has no UV-map'
level_visual_no_hemi = 'Visual-object has no hemi layer'
level_visual_no_light = 'Visual-object has no light layer'
level_light_not_spec = '"Light" parameter for the material is not specified'

# level export glow
level_no_glow = 'Level-object has no glow-objects'
level_bad_glow_type = 'Glow-object is not a mesh'
level_bad_glow = 'Glow mesh-object has no faces'
level_no_mat_glow = 'Glow-object has no material'
level_glow_empty_mat = 'Glow-object has empty material slot'
level_glow_many_mats = 'Glow-object has more than one material'
level_bad_glow_radius = 'Glow object has radius close to zero'

# level export portal
level_portal_is_no_mesh = 'Portal-object is not a mesh'
level_portal_no_vert = 'Portal mesh-object has no vertices'
level_portal_bad = 'Portal mesh-object has less than 3 vertices'
level_portal_many_verts = 'Portal mesh-object must have no more than 6 vertices'
level_portal_no_faces = 'Portal mesh-object has no polygons'
level_portal_many_faces = 'Portal mesh-object must have no more than 1 polygon'
level_portal_no_front = 'Portal "Sector Front" object not specified'
level_portal_no_back = 'Portal "Sector Back" object not specified'

# level cform export
level_bad_cform_type = 'Cform-object is not mesh'
level_cform_no_geom = 'Cform-object has no polygons'
level_cform_no_mats = 'Cform-object has no materials'
level_cform_empty_mat_slot = 'Cform-object has empty material slot'

# object export main
object_nonexp_group_verts = 'Mesh-object has vertices that are not tied to any exportable bones'
object_ungroupped_verts = 'Mesh-object has vertices that don\'t have vertex groups'
object_duplicate_bones = 'Object has duplicate bones'
object_many_arms = 'Root-object has more than one armature'
object_no_meshes = 'Root-object has no meshes'
object_skel_many_meshes = 'Skeletal object has more than one mesh'
object_bad_boneparts = 'Not all bones are tied to the bone part'
object_many_parents = 'Armature object has more than one parent'
object_no_roots = 'No root-objects found'
object_many_roots = 'Too many root-objects found, but none selected'

# object import bone
object_unsupport_bone_ver = 'Unsupported bone format version'

# object import main
object_unsupport_format_ver = 'Unsupported OBJECT format version'

# object import mesh
object_unsupport_mesh_ver = 'Unsupported mesh format version'
object_bad_vmap = 'Unsupported vertex map type'
object_many_duplicated_faces = 'Too many duplicated polygons'

# ogf import
ogf_bad_ver = 'Unsupported OGF format version'
ogf_bad_vertex_fmt = 'Unsupported OGF vertex format'
ogf_bad_model_type = 'Unsupported OGF model type'

# ogf export
ogf_has_no_arm = 'Skeletal mesh-object has no armature'
ogf_verts_count_limit = 'Too many vertices were created when saving to OGF'

# omf export
omf_empty = 'Use different export mode. This OMF-file is empty'
omf_no_anims = 'OMF-file does not have an animation block'
omf_no_params = 'OMF-file does not have an parameters block'
omf_bone_no_group = 'Not all bones in an armature have bone group'
omf_nothing_exp = 'Nothing is exported!'

# omf import
omf_no_bone = 'Armature does not have all bones that file has'
omf_nothing = 'Nothing was imported. Change import settings'
omf_nothing_imp = 'Nothing is imported!'

# omf merge
few_files = 'More than one file needs to be selected'
omf_merge_parts_count = 'File have different boneparts count'

# scene import
scene_incorrect_file = 'Invalid *.level file'
scene_err_info = 'For detailed information please follow this link:'
scene_bad_file = 'Bad scene selection file. Cannot find "scene version" chunk'
scene_obj_tool_ver = 'Unsupported object tools version'
scene_obj_count = 'Bad scene selection file. Cannot find "scene objects count" chunk'
scene_scn_objs = 'Bad scene selection file. Cannot find "scene objects" chunk'
scene_objs = 'Bad scene selection file. Cannot find "objects" chunk'
scene_no_ver = 'Bad scene selection file. Cannot find "version" chunk'
scene_ver_size = 'Bad scene selection file. "version" chunk size is not equal to 4'
scene_ver = 'Unsupported format version'
scene_obj_ver = 'Unsupported scene object format version'

# part import
part_no_objs = 'File has no objects!'

# motion
motion_shape = 'Unsupported keyframe shapes'
motion_ver = 'Unsupported motions version'
