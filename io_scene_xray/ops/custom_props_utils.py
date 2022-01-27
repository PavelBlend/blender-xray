# blender modules
import bpy

# addon modules
from .. import prefs
from .. import utils
from .. import version_utils


def find_data(operator, context):
    objects = set()
    meshes = set()
    materials = set()
    armatures = set()
    actions = set()

    # find objects
    if operator.edit_data in ('OBJECT', 'ALL'):
        if operator.edit_mode == 'ACTIVE':
            objects.add(context.object)
        elif operator.edit_mode == 'SELECTED':
            for obj in context.selected_objects:
                objects.add(obj)
        elif operator.edit_mode == 'ALL':
            for obj in bpy.data.objects:
                objects.add(obj)

    # find meshes
    if operator.edit_data in ('MESH', 'ALL'):
        if operator.edit_mode == 'ACTIVE':
            if context.object.type == 'MESH':
                meshes.add(context.object.data)
        elif operator.edit_mode == 'SELECTED':
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    meshes.add(obj.data)
        elif operator.edit_mode == 'ALL':
            for mesh in bpy.data.meshes:
                meshes.add(mesh)

    # find materials
    if operator.edit_data in ('MATERIAL', 'ALL'):
        if operator.edit_mode == 'ACTIVE':
            if context.object.type == 'MESH':
                materials.add(context.object.active_material)
        elif operator.edit_mode == 'SELECTED':
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    for material in obj.data.materials:
                        materials.add(material)
        elif operator.edit_mode == 'ALL':
            for material in bpy.data.materials:
                materials.add(material)

    # find bones
    if operator.edit_data in ('BONE', 'ALL'):
        if operator.edit_mode == 'ACTIVE':
            if context.object.type == 'ARMATURE':
                armatures.add(context.object)
        elif operator.edit_mode == 'SELECTED':
            for obj in context.selected_objects:
                if obj.type == 'ARMATURE':
                    armatures.add(obj)
        elif operator.edit_mode == 'ALL':
            for obj in bpy.data.objects:
                if obj.type == 'ARMATURE':
                    armatures.add(obj)

    # find actions
    if operator.edit_data in ('ACTION', 'ALL'):
        if operator.edit_mode == 'ACTIVE':
            if context.object.animation_data:
                actions.add(context.object.animation_data.action)
        elif operator.edit_mode == 'SELECTED':
            for obj in context.selected_objects:
                for motion in obj.xray.motions_collection:
                    action = bpy.data.actions.get(motion.name)
                    if action:
                        actions.add(action)
                if obj.animation_data:
                    actions.add(obj.animation_data.action)
        elif operator.edit_mode == 'ALL':
            for action in bpy.data.actions:
                actions.add(action)

    for collection in (objects, meshes, materials, armatures, actions):
        if None in collection:
            collection.remove(None)

    return objects, meshes, materials, armatures, actions


def draw_function(self, context):
    lay = self.layout
    col = lay.column(align=True)
    col.label(text='Edit Data:')
    col.prop(self, 'edit_data', expand=True)
    col.label(text='Edit Mode:')
    col.prop(self, 'edit_mode', expand=True)


edit_data_items = (
    ('ALL', 'All', ''),
    ('OBJECT', 'Object', ''),
    ('MESH', 'Mesh', ''),
    ('MATERIAL', 'Material', ''),
    ('BONE', 'Bone', ''),
    ('ACTION', 'Action', '')
)
edit_mode_items = (
    ('ALL', 'All', ''),
    ('SELECTED', 'Selected Objects', ''),
    ('ACTIVE', 'Active Object', '')
)
op_props = {
    # custom properties utils
    'edit_data': bpy.props.EnumProperty(
        name='Edit Data',
        items=edit_data_items,
        default='ALL'
    ),
    'edit_mode': bpy.props.EnumProperty(
        name='Edit Mode',
        items=edit_mode_items,
        default='SELECTED'
    )
}


class XRAY_OT_set_custom_to_xray_props(bpy.types.Operator):
    bl_idname = 'io_scene_xray.set_custom_to_xray_properties'
    bl_label = 'Set Custom to X-Ray'
    bl_options = {'REGISTER', 'UNDO'}

    props = op_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    draw = draw_function

    def set_custom(self, owner, prop, custom):
        if not self.obj.get(custom, None) is None:
            setattr(owner, prop, self.obj[custom])

    @utils.set_cursor_state
    def execute(self, context):
        preferences = version_utils.get_preferences()
        stgs = preferences.custom_props    # settings
        objects, meshes, materials, armatures, actions = find_data(self, context)
        # object
        for obj in objects:
            self.obj = obj
            xray = obj.xray
            self.set_custom(xray, 'flags', stgs.object_flags)
            self.set_custom(xray, 'userdata', stgs.object_userdata)
            self.set_custom(xray, 'lodref', stgs.object_lod_reference)
            self.set_custom(xray.revision, 'owner', stgs.object_owner_name)
            self.set_custom(xray.revision, 'ctime', stgs.object_creation_time)
            self.set_custom(xray.revision, 'moder', stgs.object_modif_name)
            self.set_custom(xray.revision, 'mtime', stgs.object_modified_time)
            motion_refs = obj.get(stgs.object_motion_references, None)
            if not motion_refs is None:
                motion_refs_list = motion_refs.split(',')
                for motion_ref in motion_refs_list:
                    xray.motionrefs_collection.add().name = motion_ref
        # mesh
        for mesh in meshes:
            self.obj = mesh
            self.set_custom(mesh.xray, 'flags', stgs.mesh_flags)
        # material
        for material in materials:
            self.obj = material
            xray = material.xray
            self.set_custom(xray, 'flags_twosided', stgs.material_two_sided)
            self.set_custom(xray, 'eshader', stgs.material_shader)
            self.set_custom(xray, 'cshader', stgs.material_compile)
            self.set_custom(xray, 'gamemtl', stgs.material_game_mtl)
        # bone
        for armature in armatures:
            for bone in armature.data.bones:
                self.obj = bone
                xray = bone.xray
                if not xray.exportable:
                    continue
                self.set_custom(xray, 'gamemtl', stgs.bone_game_mtl)
                self.set_custom(xray, 'length', stgs.bone_length)
                self.set_custom(xray.shape, 'type', stgs.bone_shape_type)
                self.set_custom(xray.shape, 'flags', stgs.bone_shape_flags)
                self.set_custom(xray.shape, 'box_rot', stgs.bone_box_shape_rotation)
                self.set_custom(xray.shape, 'box_trn', stgs.bone_box_shape_translate)
                self.set_custom(xray.shape, 'box_hsz', stgs.bone_box_shape_half_size)
                self.set_custom(xray.shape, 'sph_pos', stgs.bone_sphere_shape_position)
                self.set_custom(xray.shape, 'sph_rad', stgs.bone_sphere_shape_radius)
                self.set_custom(xray.shape, 'cyl_pos', stgs.bone_cylinder_shape_position)
                self.set_custom(xray.shape, 'cyl_dir', stgs.bone_cylinder_shape_direction)
                self.set_custom(xray.shape, 'cyl_hgh', stgs.bone_cylinder_shape_hight)
                self.set_custom(xray.shape, 'cyl_rad', stgs.bone_cylinder_shape_radius)
                self.set_custom(xray.ikjoint, 'type', stgs.bone_ik_joint_type)
                self.set_custom(xray.ikjoint, 'lim_x_min', stgs.bone_limit_x_min)
                self.set_custom(xray.ikjoint, 'lim_x_max', stgs.bone_limit_x_max)
                self.set_custom(xray.ikjoint, 'lim_y_min', stgs.bone_limit_y_min)
                self.set_custom(xray.ikjoint, 'lim_y_max', stgs.bone_limit_y_max)
                self.set_custom(xray.ikjoint, 'lim_z_min', stgs.bone_limit_z_min)
                self.set_custom(xray.ikjoint, 'lim_z_max', stgs.bone_limit_z_max)
                self.set_custom(xray.ikjoint, 'lim_x_spr', stgs.bone_limit_x_spring)
                self.set_custom(xray.ikjoint, 'lim_y_spr', stgs.bone_limit_y_spring)
                self.set_custom(xray.ikjoint, 'lim_z_spr', stgs.bone_limit_z_spring)
                self.set_custom(xray.ikjoint, 'lim_x_dmp', stgs.bone_limit_x_damping)
                self.set_custom(xray.ikjoint, 'lim_y_dmp', stgs.bone_limit_y_damping)
                self.set_custom(xray.ikjoint, 'lim_z_dmp', stgs.bone_limit_z_damping)
                self.set_custom(xray.ikjoint, 'spring', stgs.bone_spring)
                self.set_custom(xray.ikjoint, 'damping', stgs.bone_damping)
                self.set_custom(xray.mass, 'value', stgs.bone_mass)
                self.set_custom(xray.mass, 'center', stgs.bone_center_of_mass)
                self.set_custom(xray, 'ikflags', stgs.bone_ik_flags)
                self.set_custom(xray.breakf, 'force', stgs.bone_breakable_force)
                self.set_custom(xray.breakf, 'torque', stgs.bone_breakable_torque)
                self.set_custom(xray, 'friction', stgs.bone_friction)
                bone_group_name = bone.get(stgs.bone_part, None)
                if not bone_group_name is None:
                    group = armature.pose.bone_groups.get(bone_group_name)
                    if not group:
                        group = armature.pose.bone_groups.new(name=bone_group_name)
                    armature.pose.bones[bone.name].bone_group = group
        # action
        for action in actions:
            self.obj = action
            xray = action.xray
            self.set_custom(xray, 'fps', stgs.action_fps)
            self.set_custom(xray, 'speed', stgs.action_speed)
            self.set_custom(xray, 'accrue', stgs.action_accrue)
            self.set_custom(xray, 'falloff', stgs.action_falloff)
            self.set_custom(xray, 'bonepart', stgs.action_bone_part)
            self.set_custom(xray, 'flags', stgs.action_flags)
            self.set_custom(xray, 'power', stgs.action_power)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_set_xray_to_custom_props(bpy.types.Operator):
    bl_idname = 'io_scene_xray.set_xray_to_custom_properties'
    bl_label = 'Set X-Ray to Custom'
    bl_options = {'REGISTER', 'UNDO'}

    props = op_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    draw = draw_function

    @utils.set_cursor_state
    def execute(self, context):
        preferences = version_utils.get_preferences()
        stgs = preferences.custom_props    # settings
        objects, meshes, materials, armatures, actions = find_data(self, context)
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
                if motion_ref.name:
                    motion_refs.append(motion_ref.name)
            if motion_refs:
                obj[stgs.object_motion_references] = ','.join(motion_refs)
            else:
                obj[stgs.object_motion_references] = ''
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
            for bone in armature.data.bones:
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
                bone_group = armature.pose.bones[bone.name].bone_group
                if bone_group:
                    bone[stgs.bone_part] = bone_group.name
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

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_remove_xray_custom_props(bpy.types.Operator):
    bl_idname = 'io_scene_xray.remove_xray_custom_props'
    bl_label = 'Remove X-Ray Custom Properties'
    bl_options = {'REGISTER', 'UNDO'}

    props = op_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    draw = draw_function

    @utils.set_cursor_state
    def execute(self, context):
        preferences = version_utils.get_preferences()
        objects, meshes, materials, armatures, actions = find_data(self, context)
        bones = set()
        for armature in armatures:
            for bone in armature.data.bones:
                xray = bone.xray
                if not xray.exportable:
                    continue
                bones.add(bone)
        data = (
            (objects, prefs.props.custom_object_props),
            (meshes, prefs.props.custom_mesh_props),
            (materials, prefs.props.custom_material_props),
            (bones, prefs.props.custom_bone_props),
            (actions, prefs.props.custom_action_props)
        )
        for bpy_data_list, custom_props_dict in data:
            custom_props = custom_props_dict.keys()
            props_names = []
            for prop_id in custom_props:
                prop_name = getattr(preferences.custom_props, prop_id, None)
                if not prop_name is None:
                    props_names.append(prop_name)
            for bpy_data in bpy_data_list:
                for prop_name in props_names:
                    if not bpy_data.get(prop_name, None) is None:
                        del bpy_data[prop_name]
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_remove_all_custom_props(bpy.types.Operator):
    bl_idname = 'io_scene_xray.remove_all_custom_props'
    bl_label = 'Remove All Custom Properties'
    bl_options = {'REGISTER', 'UNDO'}

    props = op_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    draw = draw_function

    @utils.set_cursor_state
    def execute(self, context):
        objects, meshes, materials, armatures, actions = find_data(self, context)
        data_list = []
        data_list.extend(objects)
        data_list.extend(meshes)
        data_list.extend(materials)
        data_list.extend(actions)
        for armature in armatures:
            for bone in armature.data.bones:
                xray = bone.xray
                if not xray.exportable:
                    continue
                data_list.append(bone)
        for data in data_list:
            for prop in data.keys():
                if prop.startswith('cycles'):
                    continue
                if prop == 'xray':
                    continue
                del data[prop]
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


classes = (
    XRAY_OT_set_custom_to_xray_props,
    XRAY_OT_set_xray_to_custom_props,
    XRAY_OT_remove_xray_custom_props,
    XRAY_OT_remove_all_custom_props
)


def register():
    version_utils.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
