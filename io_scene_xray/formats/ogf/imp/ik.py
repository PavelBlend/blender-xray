# blender modules
import bpy
import mathutils

# addon modules
from ... import motions
from .... import rw
from .... import utils
from .... import text
from .... import log


def import_ik_data(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.S_IKDATA, None)
    if not chunk_data:
        return
    packed_reader = rw.read.PackedReader(chunk_data)
    armature = bpy.data.armatures.new(name=visual.name)
    utils.version.set_arm_display_type(armature)
    arm_obj = bpy.data.objects.new(visual.name, armature)
    utils.version.set_object_show_xray(arm_obj, True)
    arm_obj.xray.isroot = True
    utils.version.link_object(arm_obj)
    utils.version.set_active_object(arm_obj)
    # motion references
    if visual.motion_refs:
        for motion_ref in visual.motion_refs:
            ref = arm_obj.xray.motionrefs_collection.add()
            ref.name = motion_ref
    revision = arm_obj.xray.revision
    revision.owner = visual.create_name
    revision.ctime = visual.create_time
    revision.moder = visual.modif_name
    revision.mtime = visual.modif_time
    if visual.user_data:
        arm_obj.xray.userdata = visual.user_data
    if visual.lod:
        arm_obj.xray.lodref = visual.lod
    bpy.ops.object.mode_set(mode='EDIT')
    bone_props = []
    armature_bones = {}
    for bone_index, (bone_name, parent_name) in enumerate(visual.bones):
        version = packed_reader.getf('<I')[0]
        props = []
        game_material = packed_reader.gets()
        shape_type = packed_reader.getf('<H')[0]
        shape_flags = packed_reader.getf('<H')[0]
        props.extend((
            game_material,
            shape_type,
            shape_flags
        ))
        # box shape
        box_shape_rotation = packed_reader.getf('<9f')
        box_shape_translation = packed_reader.getf('<3f')
        box_shape_half_size = packed_reader.getf('<3f')
        props.extend((
            box_shape_rotation,
            box_shape_translation,
            box_shape_half_size
        ))
        # sphere shape
        sphere_shape_translation = packed_reader.getf('<3f')
        sphere_shape_radius = packed_reader.getf('<f')[0]
        props.extend((
            sphere_shape_translation,
            sphere_shape_radius
        ))
        # cylinder shape
        cylinder_shape_translation = packed_reader.getf('<3f')
        cylinder_shape_direction = packed_reader.getf('<3f')
        cylinder_shape_height = packed_reader.getf('<f')[0]
        cylinder_shape_radius = packed_reader.getf('<f')[0]
        props.extend((
            cylinder_shape_translation,
            cylinder_shape_direction,
            cylinder_shape_height,
            cylinder_shape_radius
        ))

        joint_type = packed_reader.getf('<I')[0]
        props.append(joint_type)

        # x limits
        limit_x_min, limit_x_max = packed_reader.getf('<2f')
        limit_x_spring = packed_reader.getf('<f')[0]
        limit_x_damping = packed_reader.getf('<f')[0]
        props.extend((
            limit_x_min,
            limit_x_max,
            limit_x_spring,
            limit_x_damping
        ))
        # y limits
        limit_y_min, limit_y_max = packed_reader.getf('<2f')
        limit_y_spring = packed_reader.getf('<f')[0]
        limit_y_damping = packed_reader.getf('<f')[0]
        props.extend((
            limit_y_min,
            limit_y_max,
            limit_y_spring,
            limit_y_damping
        ))
        # z limits
        limit_z_min, limit_z_max = packed_reader.getf('<2f')
        limit_z_spring = packed_reader.getf('<f')[0]
        limit_z_damping = packed_reader.getf('<f')[0]
        props.extend((
            limit_z_min,
            limit_z_max,
            limit_z_spring,
            limit_z_damping
        ))

        joint_spring = packed_reader.getf('<f')[0]
        joint_damping = packed_reader.getf('<f')[0]
        ik_flags = packed_reader.getf('<I')[0]
        breakable_force = packed_reader.getf('<f')[0]
        breakable_torque = packed_reader.getf('<f')[0]
        friction = packed_reader.getf('<f')[0]
        props.extend((
            joint_spring,
            joint_damping,
            ik_flags,
            breakable_force,
            breakable_torque,
            friction
        ))

        # bind pose
        bind_rotation = packed_reader.getv3f()
        bind_translation = packed_reader.getv3f()

        # mass
        mass_value = packed_reader.getf('<f')[0]
        mass_center = packed_reader.getv3f()
        props.extend((
            mass_value,
            mass_center,
        ))

        bone_props.append(props)

        # create bone
        bpy_bone = armature.edit_bones.new(name=bone_name)
        armature_bones[bone_index] = bpy_bone.name
        rotation = mathutils.Euler(
            (-bind_rotation[0], -bind_rotation[1], -bind_rotation[2]), 'YXZ'
        ).to_matrix().to_4x4()
        translation = mathutils.Matrix.Translation(bind_translation)
        mat = utils.version.multiply(
            translation,
            rotation,
            motions.const.MATRIX_BONE
        )
        if parent_name:
            bpy_bone.parent = armature.edit_bones.get(parent_name, None)
            if bpy_bone.parent:
                mat = utils.version.multiply(
                    bpy_bone.parent.matrix,
                    motions.const.MATRIX_BONE_INVERTED,
                    mat
                )
            else:
                log.warn(
                    text.warn.no_bone_parent,
                    bone=bone_name,
                    parent=parent_name
                )
        bpy_bone.tail.y = 0.02
        bpy_bone.matrix = mat

    bpy.ops.object.mode_set(mode='OBJECT')

    for bone_index, props in enumerate(bone_props):
        bone_name = armature_bones[bone_index]
        bone = armature.bones[bone_name]
        xray = bone.xray
        shape = xray.shape
        ik = xray.ikjoint
        shape.set_curver()
        i = 0
        xray.gamemtl = props[i]
        i += 1
        if props[i] <= 3:
            shape.type = str(props[i])
        else:
            log.warn(
                text.warn.ogf_bad_shape,
                file=visual.file_path,
                bone=bone.name
            )
        i += 1
        shape.flags = props[i]
        i += 1
        shape.box_rot = props[i]
        i += 1
        shape.box_trn = props[i]
        i += 1
        shape.box_hsz = props[i]
        i += 1
        shape.sph_pos = props[i]
        i += 1
        shape.sph_rad = props[i]
        i += 1
        shape.cyl_pos = props[i]
        i += 1
        shape.cyl_dir = props[i]
        i += 1
        shape.cyl_hgh = props[i]
        i += 1
        shape.cyl_rad = props[i]
        i += 1
        if props[i] <= 5:
            ik.type = str(props[i])
        else:
            log.warn(
                text.warn.ogf_bad_joint,
                file=visual.file_path,
                bone=bone.name
            )
        i += 1
        ik.lim_x_max = -props[i]
        i += 1
        ik.lim_x_min = -props[i]
        i += 1
        ik.lim_x_spr = props[i]
        i += 1
        ik.lim_x_dmp = props[i]
        i += 1
        ik.lim_y_max = -props[i]
        i += 1
        ik.lim_y_min = -props[i]
        i += 1
        ik.lim_y_spr = props[i]
        i += 1
        ik.lim_y_dmp = props[i]
        i += 1
        ik.lim_z_max = -props[i]
        i += 1
        ik.lim_z_min = -props[i]
        i += 1
        ik.lim_z_spr = props[i]
        i += 1
        ik.lim_z_dmp = props[i]
        i += 1
        ik.spring = props[i]
        i += 1
        ik.damping = props[i]
        i += 1
        xray.ikflags = props[i]
        i += 1
        xray.breakf.force = props[i]
        i += 1
        xray.breakf.torque = props[i]
        i += 1
        xray.friction = props[i]
        i += 1
        xray.mass.value = props[i]
        i += 1
        xray.mass.center = props[i]

    for bone in arm_obj.pose.bones:
        bone.rotation_mode = 'ZXY'
    visual.arm_obj = arm_obj
