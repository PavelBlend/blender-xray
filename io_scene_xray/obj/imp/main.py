import os
import math

import bpy
import mathutils

from ... import xray_io, xray_motions, log, utils
from .. import fmt
from . import bone, mesh


def _is_compatible_texture(texture, filepart):
    image = getattr(texture, 'image', None)
    if image is None:
        return False
    if filepart not in image.filepath:
        return False
    return True


_S_FFF = xray_io.PackedReader.prep('fff')


def read_v3f(packed_reader):
    vec = packed_reader.getp(_S_FFF)
    return vec[0], vec[2], vec[1]


def import_main(fpath, context, creader):
    object_name = os.path.basename(fpath.lower())

    bpy_arm_obj = None
    renamemap = {}
    meshes_data = None

    unread_chunks = []

    for (cid, data) in creader:
        if cid == fmt.Chunks.Object.VERSION:
            reader = xray_io.PackedReader(data)
            ver = reader.getf('H')[0]
            if ver != 0x10:
                raise utils.AppError(
                    'unsupported OBJECT format version',
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
                    flags = reader.getf('B')[0]
                    reader.skip(4 + 4)    # fvf and TCs count
                    texture = reader.gets()
                    vmap = reader.gets()
                    if texture != vmap or not (texture and vmap):
                        old_object_format = False
                        renamemap[vmap.lower()] = vmap
                    else:    # old format (Objects\Rainbow\lest.object)
                        old_object_format = True
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
                        old_object_format = False
                        renamemap[vmap.lower()] = vmap
                    else:    # old format (Objects\corps\corp_BYAKA.object)
                        old_object_format = True
                        vmap = 'Texture'
                    renamemap[vmap.lower()] = vmap
                    flags = reader.int()
                    reader.skip(4 + 4)    # fvf and ?
                bpy_material = None
                tx_filepart = texture.replace('\\', os.path.sep).lower()
                for material in bpy.data.materials:
                    if not material.name.startswith(name):
                        continue
                    if material.xray.flags != flags:
                        continue
                    if material.xray.eshader != eshader:
                        continue
                    if material.xray.cshader != cshader:
                        continue
                    if material.xray.gamemtl != gamemtl:
                        continue

                    if (not texture) and (not vmap):
                        all_empty_slots = all(
                            not slot for slot in material.texture_slots
                        )
                        if all_empty_slots:
                            bpy_material = material
                            break

                    ts_found = False
                    for slot in material.texture_slots:
                        if not slot:
                            continue
                        if slot.uv_layer != vmap:
                            continue
                        if not _is_compatible_texture(
                            slot.texture, tx_filepart
                        ):
                            continue
                        ts_found = True
                        break
                    if not ts_found:
                        continue
                    bpy_material = material
                    break
                if bpy_material is None:
                    bpy_material = bpy.data.materials.new(name)
                    bpy_material.xray.version = context.version
                    bpy_material.xray.flags = flags
                    bpy_material.xray.eshader = eshader
                    bpy_material.xray.cshader = cshader
                    bpy_material.xray.gamemtl = gamemtl
                    bpy_material.use_shadeless = True
                    bpy_material.use_transparency = True
                    bpy_material.alpha = 0
                    if texture:
                        bpy_texture = bpy.data.textures.get(texture)
                        if (bpy_texture is None) \
                            or not _is_compatible_texture(
                                bpy_texture, tx_filepart
                            ):
                            bpy_texture = bpy.data.textures.new(
                                texture, type='IMAGE'
                            )
                            bpy_texture.image = context.image(texture)
                            bpy_texture.use_preview_alpha = True
                        bpy_texture_slot = bpy_material.texture_slots.add()
                        bpy_texture_slot.texture = bpy_texture
                        bpy_texture_slot.texture_coords = 'UV'
                        bpy_texture_slot.uv_layer = vmap
                        bpy_texture_slot.use_map_color_diffuse = True
                        bpy_texture_slot.use_map_alpha = True
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
                bpy_armature.use_auto_ik = True
                bpy_armature.draw_type = 'STICK'
                bpy_arm_obj = bpy.data.objects.new(object_name, bpy_armature)
                bpy_arm_obj.show_x_ray = True
                bpy_armature.xray.joint_limits_type = 'XRAY'
                bpy.context.scene.objects.link(bpy_arm_obj)
                bpy.context.scene.objects.active = bpy_arm_obj
            if cid == fmt.Chunks.Object.BONES:
                for _ in range(bones_count):
                    name = reader.gets()
                    parent = reader.gets()
                    vmap = reader.gets()
                    offset = read_v3f(reader)
                    rotate = read_v3f(reader)
                    length = reader.getf('f')[0]
                    rotate = rotate[2], rotate[1], rotate[0]
                    bpy_bone = _create_bone(
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
                for (_, bdat) in xray_io.ChunkedReader(data):
                    bone.import_bone(
                        context,
                        xray_io.ChunkedReader(bdat),
                        bpy_arm_obj,
                        renamemap
                    )
            bpy.ops.object.mode_set(mode='EDIT')
            try:
                if context.operator.shaped_bones:
                    bones = bpy_armature.edit_bones
                    lenghts = [0] * len(bones)
                    for i, bone_ in enumerate(bones):
                        min_rad_sq = math.inf
                        for j, bone1 in enumerate(bones):
                            if j == i:
                                continue
                            rad_sq = (bone1.head - bone_.head).length_squared
                            if rad_sq < min_rad_sq:
                                min_rad_sq = rad_sq
                        lenghts[i] = math.sqrt(min_rad_sq)
                    for bone_, length in zip(bones, lenghts):
                        bone_.length = min(max(length * 0.4, 0.01), 0.1)
            finally:
                bpy.ops.object.mode_set(mode='OBJECT')
            for bone_ in bpy_arm_obj.pose.bones:
                bone_.rotation_mode = 'ZXY'
        elif cid in (
                fmt.Chunks.Object.PARTITIONS0,
                fmt.Chunks.Object.PARTITIONS1
            ):
            bpy.context.scene.objects.active = bpy_arm_obj
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
            xray_motions.import_motions(reader, bpy_arm_obj)
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
        bpy.context.scene.objects.link(mesh_)

    bpy_obj = bpy_arm_obj
    if bpy_obj is None:
        if len(mesh_objects) == 1:
            bpy_obj = mesh_objects[0]
            bpy_obj.name = object_name
        else:
            bpy_obj = bpy.data.objects.new(object_name, None)
            for mesh_ in mesh_objects:
                mesh_.parent = bpy_obj
            bpy.context.scene.objects.link(bpy_obj)

    bpy_obj.xray.version = context.version
    bpy_obj.xray.isroot = True

    if fpath.lower().startswith(
            context.objects_folder.lower()
        ) and context.objects_folder:

        object_folder_length = len(context.objects_folder)
        bpy_obj.xray.export_path = os.path.dirname(
            fpath.lower()
        )[object_folder_length : ]

    for (cid, data) in unread_chunks:
        if cid == fmt.Chunks.Object.TRANSFORM:
            reader = xray_io.PackedReader(data)
            pos = read_v3f(reader)
            rot = read_v3f(reader)
            bpy_obj.matrix_basis *= mathutils.Matrix.Translation(pos) \
                * mathutils.Euler(rot, 'YXZ').to_matrix().to_4x4()
        elif cid == fmt.Chunks.Object.FLAGS:
            length_data = len(data)
            if length_data == 4:
                bpy_obj.xray.flags = xray_io.PackedReader(data).int()
            elif length_data == 1:    # old object format
                bpy_obj.xray.flags = xray_io.PackedReader(data).getf('B')[0]
        elif cid == fmt.Chunks.Object.USERDATA:
            bpy_obj.xray.userdata = xray_io.PackedReader(
                data
            ).gets(
                onerror=lambda e: log.warn('bad userdata', error=e)
            )
        elif cid == fmt.Chunks.Object.LOD_REF:
            bpy_obj.xray.lodref = xray_io.PackedReader(data).gets()
        elif cid == fmt.Chunks.Object.REVISION:
            reader = xray_io.PackedReader(data)
            bpy_obj.xray.revision.owner = reader.gets()
            bpy_obj.xray.revision.ctime = reader.int()
            bpy_obj.xray.revision.moder = reader.gets()
            bpy_obj.xray.revision.mtime = reader.int()
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
