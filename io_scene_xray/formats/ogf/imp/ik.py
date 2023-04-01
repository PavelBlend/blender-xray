# blender modules
import bpy
import mathutils

# addon modules
from .. import fmt
from ... import motions
from .... import rw
from .... import utils
from .... import text
from .... import log


def import_ik_data(chunks, ogf_chunks, visual):
    # create reader
    read_ver = True
    chunk_data = chunks.pop(ogf_chunks.S_IKDATA_2, None)

    if not chunk_data:
        read_ver = False
        chunk_data = chunks.pop(ogf_chunks.S_IKDATA_1, None)

    if not chunk_data:
        chunk_data = chunks.pop(ogf_chunks.S_IKDATA_0, None)

    if not chunk_data:
        return

    packed_reader = rw.read.PackedReader(chunk_data)

    # create armature
    armature = bpy.data.armatures.new(name=visual.name)
    utils.version.set_arm_display_type(armature)

    # create object
    arm_obj = bpy.data.objects.new(visual.name, armature)
    arm_obj.xray.isroot = True
    utils.version.set_object_show_xray(arm_obj, True)
    utils.version.link_object(arm_obj)
    utils.version.set_active_object(arm_obj)
    visual.arm_obj = arm_obj

    # motion references
    if visual.motion_refs:
        for motion_ref in visual.motion_refs:
            ref = arm_obj.xray.motionrefs_collection.add()
            ref.name = motion_ref

    # revision
    revision = arm_obj.xray.revision
    revision.owner = visual.create_name
    revision.ctime = visual.create_time
    revision.moder = visual.modif_name
    revision.mtime = visual.modif_time

    # userdata
    if visual.user_data:
        arm_obj.xray.userdata = visual.user_data

    # lod
    if visual.lod:
        arm_obj.xray.lodref = visual.lod

    # read params and create bones
    bones_props = []
    armature_bones = {}
    bpy.ops.object.mode_set(mode='EDIT')

    for bone_index, (bone_name, parent_name) in enumerate(visual.bones):
        if read_ver:
            version = packed_reader.uint32()
        else:
            version = 0

        game_material = packed_reader.gets()

        shape_type = packed_reader.getf('<H')[0]
        shape_flags = packed_reader.getf('<H')[0]

        # box shape
        box_shape_rotation = packed_reader.getf('<9f')
        box_shape_translation = packed_reader.getf('<3f')
        box_shape_half_size = packed_reader.getf('<3f')

        # sphere shape
        sphere_shape_translation = packed_reader.getf('<3f')
        sphere_shape_radius = packed_reader.getf('<f')[0]

        # cylinder shape
        cylinder_shape_translation = packed_reader.getf('<3f')
        cylinder_shape_direction = packed_reader.getf('<3f')
        cylinder_shape_height = packed_reader.getf('<f')[0]
        cylinder_shape_radius = packed_reader.getf('<f')[0]

        joint_type = packed_reader.uint32()

        # x limits
        limit_x_min, limit_x_max = packed_reader.getf('<2f')
        limit_x_spring = packed_reader.getf('<f')[0]
        limit_x_damping = packed_reader.getf('<f')[0]

        # y limits
        limit_y_min, limit_y_max = packed_reader.getf('<2f')
        limit_y_spring = packed_reader.getf('<f')[0]
        limit_y_damping = packed_reader.getf('<f')[0]

        # z limits
        limit_z_min, limit_z_max = packed_reader.getf('<2f')
        limit_z_spring = packed_reader.getf('<f')[0]
        limit_z_damping = packed_reader.getf('<f')[0]

        joint_spring = packed_reader.getf('<f')[0]
        joint_damping = packed_reader.getf('<f')[0]
        ik_flags = packed_reader.uint32()
        breakable_force = packed_reader.getf('<f')[0]
        breakable_torque = packed_reader.getf('<f')[0]

        if version > fmt.BONE_VERSION_0:
            friction = packed_reader.getf('<f')[0]
        else:
            friction = 0

        # bind pose
        bind_rotation = packed_reader.getv3f()
        bind_translation = packed_reader.getv3f()

        # mass
        mass_value = packed_reader.getf('<f')[0]
        mass_center = packed_reader.getv3f()

        props = (
            game_material,
            shape_type,
            shape_flags,

            box_shape_rotation,
            box_shape_translation,
            box_shape_half_size,

            sphere_shape_translation,
            sphere_shape_radius,

            cylinder_shape_translation,
            cylinder_shape_direction,
            cylinder_shape_height,
            cylinder_shape_radius,

            joint_type,

            limit_x_min,
            limit_x_max,
            limit_x_spring,
            limit_x_damping,

            limit_y_min,
            limit_y_max,
            limit_y_spring,
            limit_y_damping,

            limit_z_min,
            limit_z_max,
            limit_z_spring,
            limit_z_damping,

            joint_spring,
            joint_damping,
            ik_flags,
            breakable_force,
            breakable_torque,
            friction,

            mass_value,
            mass_center
        )

        bones_props.append(props)

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

    # set bone rotation mode
    for bone in arm_obj.pose.bones:
        bone.rotation_mode = 'ZXY'

    # set xray properties
    for bone_index, props in enumerate(bones_props):
        bone_name = armature_bones[bone_index]
        bone = armature.bones[bone_name]

        xray = bone.xray
        ik = xray.ikjoint
        shape = xray.shape
        shape.set_curver()

        (
            game_material,
            shape_type,
            shape_flags,

            box_shape_rotation,
            box_shape_translation,
            box_shape_half_size,

            sphere_shape_translation,
            sphere_shape_radius,

            cylinder_shape_translation,
            cylinder_shape_direction,
            cylinder_shape_height,
            cylinder_shape_radius,

            joint_type,

            limit_x_min,
            limit_x_max,
            limit_x_spring,
            limit_x_damping,

            limit_y_min,
            limit_y_max,
            limit_y_spring,
            limit_y_damping,

            limit_z_min,
            limit_z_max,
            limit_z_spring,
            limit_z_damping,

            joint_spring,
            joint_damping,
            ik_flags,
            breakable_force,
            breakable_torque,
            friction,

            mass_value,
            mass_center
        ) = props


        xray.gamemtl = game_material

        if shape_type <= 3:
            shape.type = str(shape_type)
        else:
            log.warn(
                text.warn.ogf_bad_shape,
                file=visual.file_path,
                bone=bone.name
            )

        shape.flags = shape_flags

        shape.box_rot = box_shape_rotation
        shape.box_trn = box_shape_translation
        shape.box_hsz = box_shape_half_size

        shape.sph_pos = sphere_shape_translation
        shape.sph_rad = sphere_shape_radius

        shape.cyl_pos = cylinder_shape_translation
        shape.cyl_dir = cylinder_shape_direction
        shape.cyl_hgh = cylinder_shape_height
        shape.cyl_rad = cylinder_shape_radius

        if joint_type <= 5:
            ik.type = str(joint_type)
        else:
            log.warn(
                text.warn.ogf_bad_joint,
                file=visual.file_path,
                bone=bone.name
            )

        # x-limits
        ik.lim_x_max = -limit_x_min
        ik.lim_x_min = -limit_x_max

        ik.lim_x_spr = limit_x_spring
        ik.lim_x_dmp = limit_x_damping

        # y-limits
        ik.lim_y_max = -limit_y_min
        ik.lim_y_min = -limit_y_max

        ik.lim_y_spr = limit_y_spring
        ik.lim_y_dmp = limit_y_damping

        # z-limits
        ik.lim_z_max = -limit_z_min
        ik.lim_z_min = -limit_z_max

        ik.lim_z_spr = limit_z_spring
        ik.lim_z_dmp = limit_z_damping

        ik.spring = joint_spring
        ik.damping = joint_damping

        xray.ikflags = ik_flags

        xray.breakf.force = breakable_force
        xray.breakf.torque = breakable_torque

        xray.friction = friction

        xray.mass.value = mass_value
        xray.mass.center = mass_center
