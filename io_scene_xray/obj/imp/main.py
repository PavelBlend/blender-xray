# standart modules
import os
import math

# blender modules
import bpy
import mathutils

# addon modules
from . import bone
from . import mesh
from .. import fmt
from ... import text
from ... import data_blocks
from ... import skl
from ... import log
from ... import utils
from ... import xray_io
from ... import motions


def import_main(file_path, context, creader):
    object_name = os.path.basename(file_path.lower())

    bpy_arm_obj = None
    renamemap = {}
    meshes_data = None

    unread_chunks = []

    for (cid, data) in creader:
        if cid == fmt.Chunks.Object.VERSION:
            reader = xray_io.PackedReader(data)
            ver = reader.getf('<H')[0]
            if ver != fmt.CURRENT_OBJECT_VERSION:
                raise log.AppError(
                    text.error.object_unsupport_format_ver,
                    log.props(version=ver)
                )
        elif cid == fmt.Chunks.Object.MESHES:
            meshes_data = data
        elif cid in (
                fmt.Chunks.Object.SURFACES,
                fmt.Chunks.Object.SURFACES1,
                fmt.Chunks.Object.SURFACES2
            ):

            reader = xray_io.PackedReader(data)
            surfaces_count = reader.int()
            if cid == fmt.Chunks.Object.SURFACES:
                try:
                    xrlc_reader = xray_io.PackedReader(
                        creader.next(fmt.Chunks.Object.SURFACES_XRLC)
                    )
                    xrlc_shaders = [
                        xrlc_reader.gets() for _ in range(surfaces_count)
                    ]
                except:
                    xrlc_shaders = ['default' for _ in range(surfaces_count)]
            for surface_index in range(surfaces_count):
                if cid == fmt.Chunks.Object.SURFACES:
                    name = reader.gets()
                    eshader = reader.gets()
                    flags = reader.getf('<B')[0]
                    reader.skip(4 + 4)    # fvf and TCs count
                    texture = reader.gets()
                    vmap = reader.gets()
                    if texture != vmap or not (texture and vmap):
                        renamemap[vmap.lower()] = vmap
                    else:    # old format (Objects\Rainbow\lest.object)
                        vmap = 'Texture'
                    gamemtl = 'default'
                    cshader = xrlc_shaders[surface_index]
                else:
                    name = reader.gets()
                    eshader = reader.gets()
                    cshader = reader.gets()
                    gamemtl = reader.gets() \
                        if cid == fmt.Chunks.Object.SURFACES2 \
                        else 'default'
                    texture = reader.gets()
                    vmap = reader.gets()
                    if texture != vmap or not (texture and vmap):
                        renamemap[vmap.lower()] = vmap
                    else:    # old format (Objects\corps\corp_BYAKA.object)
                        vmap = 'Texture'
                    renamemap[vmap.lower()] = vmap
                    flags = reader.int()
                    reader.skip(4 + 4)    # fvf and ?
                bpy_material, bpy_image = data_blocks.material.get_material(
                    context,
                    name,
                    texture,
                    eshader,
                    cshader,
                    gamemtl,
                    flags,
                    vmap
                )
                context.loaded_materials[name] = bpy_material
        elif cid in (
                fmt.Chunks.Object.BONES,
                fmt.Chunks.Object.BONES1
            ):
            if cid == fmt.Chunks.Object.BONES:
                reader = xray_io.PackedReader(data)
                bones_count = reader.int()
                if not bones_count:
                    continue    # Do not create an armature if zero bones
            if bpy and (bpy_arm_obj is None):
                bpy_armature = bpy.data.armatures.new(object_name)
                utils.version.set_arm_display_type(bpy_armature)
                bpy_arm_obj = bpy.data.objects.new(object_name, bpy_armature)
                bpy_armature.xray.joint_limits_type = 'XRAY'
                utils.version.set_object_show_xray(bpy_arm_obj, True)
                if not utils.version.IS_28:
                    bpy_armature.use_auto_ik = True
                utils.version.link_object(bpy_arm_obj)
                utils.version.set_active_object(bpy_arm_obj)
            if cid == fmt.Chunks.Object.BONES:
                for _ in range(bones_count):
                    name = reader.gets()
                    parent = reader.gets()
                    vmap = reader.gets()
                    offset = reader.getv3fp()
                    rotate = reader.getv3fp()
                    length = reader.getf('<f')[0]
                    rotate = rotate[2], rotate[1], rotate[0]
                    bpy_bone = bone.create_bone(
                        context, bpy_arm_obj,
                        name, parent, vmap,
                        offset, rotate, length,
                        renamemap
                    )
                    xray = bpy_bone.xray
                    xray.mass.gamemtl = 'default_object'
                    xray.mass.value = 10
                    ik = xray.ikjoint

                    ik.lim_x_min, ik.lim_x_max = 0, 0
                    ik.lim_x_spr, ik.lim_x_dmp = 1, 1

                    ik.lim_y_min, ik.lim_y_max = 0, 0
                    ik.lim_y_spr, ik.lim_y_dmp = 1, 1

                    ik.lim_z_min, ik.lim_z_max = 0, 0
                    ik.lim_z_spr, ik.lim_z_dmp = 1, 1

                    ik.spring = 1
                    ik.damping = 1
            else:
                bones_chunks = []
                bone_id_by_name = {}
                bones_reader = xray_io.ChunkedReader(data)
                for index, (_, bone_data) in enumerate(bones_reader):
                    bone_chunks = utils.get_chunks(bone_data)
                    def_data = bone_chunks[fmt.Chunks.Bone.DEF]
                    def_reader = xray_io.PackedReader(def_data)
                    bone_name = def_reader.gets()
                    bones_chunks.append(bone_chunks)
                    bone_id_by_name[bone_name] = index
                imported_bones = set()
                for bone_chunks in bones_chunks:
                    bone.import_bone(
                        context,
                        bone_chunks,
                        bpy_arm_obj,
                        renamemap,
                        imported_bones,
                        bones_chunks,
                        bone_id_by_name
                    )
            for bone_ in bpy_arm_obj.pose.bones:
                bone_.rotation_mode = 'ZXY'
        elif cid in (
                fmt.Chunks.Object.PARTITIONS0,
                fmt.Chunks.Object.PARTITIONS1
            ):
            utils.version.set_active_object(bpy_arm_obj)
            bpy.ops.object.mode_set(mode='POSE')
            try:
                reader = xray_io.PackedReader(data)
                for _partition_idx in range(reader.int()):
                    bpy.ops.pose.group_add()
                    bone_group = bpy_arm_obj.pose.bone_groups.active
                    bone_group.name = reader.gets()
                    for _bone_idx in range(reader.int()):
                        name = reader.gets() \
                            if cid == fmt.Chunks.Object.PARTITIONS1 \
                            else reader.int()
                        bpy_arm_obj.pose.bones[name].bone_group = bone_group
            finally:
                bpy.ops.object.mode_set(mode='OBJECT')
        elif cid == fmt.Chunks.Object.MOTIONS:
            if not context.import_motions:
                continue
            reader = xray_io.PackedReader(data)
            skl_context = skl.imp.ImportSklContext()
            skl_context.bpy_arm_obj=bpy_arm_obj
            skl_context.motions_filter=motions.utilites.MOTIONS_FILTER_ALL
            skl_context.add_actions_to_motion_list = True
            skl_context.filename=object_name
            motions.imp.import_motions(reader, skl_context)
        elif cid == fmt.Chunks.Object.LIB_VERSION:
            pass  # skip obsolete chunk
        else:
            unread_chunks.append((cid, data))

    mesh_objects = []
    for (_, mdat) in xray_io.ChunkedReader(meshes_data):
        mesh_ = mesh.import_mesh(
            context, xray_io.ChunkedReader(mdat), renamemap
        )

        if bpy_arm_obj:
            bpy_armmod = mesh_.modifiers.new(name='Armature', type='ARMATURE')
            bpy_armmod.object = bpy_arm_obj
            mesh_.parent = bpy_arm_obj

        mesh_objects.append(mesh_)
        utils.version.link_object(mesh_)

    bpy_obj = bpy_arm_obj
    if bpy_obj is None:
        if len(mesh_objects) == 1:
            bpy_obj = mesh_objects[0]
            bpy_obj.name = object_name
        else:
            bpy_obj = bpy.data.objects.new(object_name, None)
            for mesh_ in mesh_objects:
                mesh_.parent = bpy_obj
            utils.version.link_object(bpy_obj)

    bpy_obj.xray.version = context.version
    bpy_obj.xray.isroot = True

    if file_path.lower().startswith(
            context.objects_folder.lower()
        ) and context.objects_folder:

        object_folder_length = len(context.objects_folder)
        bpy_obj.xray.export_path = os.path.dirname(
            file_path.lower()
        )[object_folder_length : ]

    for (cid, data) in unread_chunks:
        if cid == fmt.Chunks.Object.TRANSFORM:
            reader = xray_io.PackedReader(data)
            pos = reader.getv3fp()
            rot = reader.getv3fp()
            bpy_obj.matrix_basis = context.multiply(
                bpy_obj.matrix_basis,
                mathutils.Matrix.Translation(pos),
                mathutils.Euler(rot, 'YXZ').to_matrix().to_4x4()
            )
        elif cid == fmt.Chunks.Object.FLAGS:
            length_data = len(data)
            if length_data == 4:
                bpy_obj.xray.flags = xray_io.PackedReader(data).int()
            elif length_data == 1:    # old object format
                bpy_obj.xray.flags = xray_io.PackedReader(data).getf('<B')[0]
        elif cid == fmt.Chunks.Object.USERDATA:
            bpy_obj.xray.userdata = xray_io.PackedReader(
                data
            ).gets(
                onerror=lambda e: log.warn(
                    text.warn.object_bad_userdata,
                    error=str(e),
                    file=file_path
                )
            )
        elif cid == fmt.Chunks.Object.LOD_REF:
            bpy_obj.xray.lodref = xray_io.PackedReader(data).gets()
        elif cid == fmt.Chunks.Object.REVISION:
            reader = xray_io.PackedReader(data)
            bpy_obj.xray.revision.owner = reader.gets()
            bpy_obj.xray.revision.ctime = reader.getf('<i')[0]
            bpy_obj.xray.revision.moder = reader.gets()
            bpy_obj.xray.revision.mtime = reader.getf('<i')[0]
        elif cid == fmt.Chunks.Object.MOTION_REFS:
            mrefs = bpy_obj.xray.motionrefs_collection
            for mref in xray_io.PackedReader(data).gets().split(','):
                mrefs.add().name = mref
        elif cid == fmt.Chunks.Object.SMOTIONS3:
            reader = xray_io.PackedReader(data)
            mrefs = bpy_obj.xray.motionrefs_collection
            for _ in range(reader.int()):
                mrefs.add().name = reader.gets()
        else:
            log.debug('unknown chunk', cid=cid)

    return bpy_obj
