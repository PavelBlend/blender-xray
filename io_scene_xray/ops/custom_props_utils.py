# blender modules
import bpy

# addon modules
from .. import plugin_prefs


def find_data(context):
    scn = context.scene.xray
    objects = set()
    meshes = set()
    materials = set()
    armatures = set()
    actions = set()

    # find objects
    if scn.custom_properties_edit_data in ('OBJECT', 'ALL'):
        if scn.custom_properties_edit_mode == 'ACTIVE':
            objects.add(context.object)
        elif scn.custom_properties_edit_mode == 'SELECTED':
            for obj in context.selected_objects:
                objects.add(obj)
        elif scn.custom_properties_edit_mode == 'ALL':
            for obj in bpy.data.objects:
                objects.add(obj)

    # find meshes
    if scn.custom_properties_edit_data in ('MESH', 'ALL'):
        if scn.custom_properties_edit_mode == 'ACTIVE':
            if context.object.type == 'MESH':
                meshes.add(context.object.data)
        elif scn.custom_properties_edit_mode == 'SELECTED':
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    meshes.add(obj.data)
        elif scn.custom_properties_edit_mode == 'ALL':
            for mesh in bpy.data.meshes:
                meshes.add(mesh)

    # find materials
    if scn.custom_properties_edit_data in ('MATERIAL', 'ALL'):
        if scn.custom_properties_edit_mode == 'ACTIVE':
            materials.add(context.object.active_material)
        elif scn.custom_properties_edit_mode == 'SELECTED':
            for obj in context.selected_objects:
                for material in obj.data.materials:
                    materials.add(material)
        elif scn.custom_properties_edit_mode == 'ALL':
            for material in bpy.data.materials:
                materials.add(material)

    # find bones
    if scn.custom_properties_edit_data in ('ARMATURE', 'ALL'):
        if scn.custom_properties_edit_mode == 'ACTIVE':
            if context.object.type == 'ARMATURE':
                armatures.add(context.object.data)
        elif scn.custom_properties_edit_mode == 'SELECTED':
            for obj in context.selected_objects:
                if obj.type == 'ARMATURE':
                    armatures.add(obj.data)
        elif scn.custom_properties_edit_mode == 'ALL':
            for armature in bpy.data.armatures:
                armatures.add(armature)

    # find actions
    if scn.custom_properties_edit_data in ('ACTION', 'ALL'):
        if scn.custom_properties_edit_mode == 'ACTIVE':
            if context.object.animation_data:
                actions.add(context.object.animation_data.action)
        elif scn.custom_properties_edit_mode == 'SELECTED':
            for obj in context.selected_objects:
                if obj.animation_data:
                    actions.add(obj.animation_data.action)
        elif scn.custom_properties_edit_mode == 'ALL':
            for action in bpy.data.actions:
                actions.add(action)

    return objects, meshes, materials, armatures, actions


class XRAY_OT_SetCustomToXRayProperties(bpy.types.Operator):
    bl_idname = 'io_scene_xray.set_custom_to_xray_properties'
    bl_label = 'Set Custom to X-Ray'

    def set_custom(self, prop, custom):
        if self.obj.get(custom):
            prop = self.obj[custom]

    def execute(self, context):
        prefs = plugin_prefs.get_preferences()
        custom_props = prefs.custom_props
        objects, meshes, materials, armatures, actions = find_data(context)
        for obj in objects:
            print(obj)
        return {'FINISHED'}


class XRAY_OT_SetXRayToCustomProperties(bpy.types.Operator):
    bl_idname = 'io_scene_xray.set_xray_to_custom_properties'
    bl_label = 'Set X-Ray to Custom'

    def execute(self, context):
        prefs = plugin_prefs.get_preferences()
        stgs = prefs.custom_props    # settings
        objects, meshes, materials, armatures, actions = find_data(context)
        # object
        for obj in objects:
            xray = obj.xray
            obj[stgs.object_flags] = xray.flags
            obj[stgs.object_userdata] = xray.userdata
            obj[stgs.object_lod_reference] = xray.lodref
            obj[stgs.object_owner_name] = xray.revision.owner
            obj[stgs.object_creation_time] = xray.revision.ctime
            obj[stgs.object_modif_name] = xray.revision.moder
            obj[stgs.object_modified_time] = xray.revision.mtime
            motion_refs = []
            for motion_ref in xray.motionrefs_collection:
                motion_refs.append(motion_ref.name)
            obj[stgs.object_motion_references] = ','.join(motion_refs)
        # mesh
        for mesh in meshes:
            mesh[stgs.mesh_flags] = mesh.xray.flags
        # material
        for material in materials:
            xray = material.xray
            material[stgs.material_two_sided] = xray.flags_twosided
            material[stgs.material_shader] = xray.eshader
            material[stgs.material_compile] = xray.cshader
            material[stgs.material_game_mtl] = xray.gamemtl
        # bone
        for armature in armatures:
            for bone in armature.bones:
                xray = bone.xray
                if not xray.exportable:
                    continue
                bone[stgs.bone_game_mtl] = xray.gamemtl
                bone[stgs.bone_length] = xray.length
                bone[stgs.bone_shape_type] = xray.shape.type
                bone[stgs.bone_shape_flags] = xray.shape.flags
                bone[stgs.bone_box_shape_rotation] = xray.shape.box_rot
                bone[stgs.bone_box_shape_translate] = xray.shape.box_trn
                bone[stgs.bone_box_shape_half_size] = xray.shape.box_hsz
                bone[stgs.bone_sphere_shape_position] = xray.shape.sph_pos
                bone[stgs.bone_sphere_shape_radius] = xray.shape.sph_rad
                bone[stgs.bone_cylinder_shape_position] = xray.shape.cyl_pos
                bone[stgs.bone_cylinder_shape_direction] = xray.shape.cyl_dir
                bone[stgs.bone_cylinder_shape_hight] = xray.shape.cyl_hgh
                bone[stgs.bone_cylinder_shape_radius] = xray.shape.cyl_rad
                bone[stgs.bone_ik_joint_type] = xray.ikjoint.type
                bone[stgs.bone_limit_x_min] = xray.ikjoint.lim_x_min
                bone[stgs.bone_limit_x_max] = xray.ikjoint.lim_x_max
                bone[stgs.bone_limit_y_min] = xray.ikjoint.lim_y_min
                bone[stgs.bone_limit_y_max] = xray.ikjoint.lim_y_max
                bone[stgs.bone_limit_z_min] = xray.ikjoint.lim_z_min
                bone[stgs.bone_limit_z_max] = xray.ikjoint.lim_z_max
                bone[stgs.bone_limit_x_spring] = xray.ikjoint.lim_x_spr
                bone[stgs.bone_limit_y_spring] = xray.ikjoint.lim_y_spr
                bone[stgs.bone_limit_z_spring] = xray.ikjoint.lim_z_spr
                bone[stgs.bone_limit_x_damping] = xray.ikjoint.lim_x_dmp
                bone[stgs.bone_limit_y_damping] = xray.ikjoint.lim_y_dmp
                bone[stgs.bone_limit_z_damping] = xray.ikjoint.lim_z_dmp
                bone[stgs.bone_spring] = xray.ikjoint.spring
                bone[stgs.bone_damping] = xray.ikjoint.damping
                bone[stgs.bone_mass] = xray.mass.value
                bone[stgs.bone_center_of_mass] = xray.mass.center
                bone[stgs.bone_ik_flags] = xray.ikflags
                bone[stgs.bone_breakable_force] = xray.breakf.force
                bone[stgs.bone_breakable_torque] = xray.breakf.torque
                bone[stgs.bone_friction] = xray.friction
        # action
        for action in actions:
            xray = action.xray
            action[stgs.action_fps] = xray.fps
            action[stgs.action_speed] = xray.speed
            action[stgs.action_accrue] = xray.accrue
            action[stgs.action_falloff] = xray.falloff
            action[stgs.action_bone_part] = xray.bonepart
            action[stgs.action_flags] = xray.flags
            action[stgs.action_power] = xray.power
        return {'FINISHED'}
