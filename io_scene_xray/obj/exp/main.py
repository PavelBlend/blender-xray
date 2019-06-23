import platform
import getpass
import time

import bpy
import mathutils

from ... import xray_io, utils, log, xray_motions
from ...version_utils import IS_28
from .. import fmt
from . import mesh, bone


def pw_v3f(vec):
    return vec[0], vec[2], vec[1]


def export_version(chunked_writer):
    chunked_writer.put(
        fmt.Chunks.Object.VERSION,
        xray_io.PackedWriter().putf('H', 0x10)
    )


def export_flags(chunked_writer, xray):
    chunked_writer.put(
        fmt.Chunks.Object.FLAGS,
        xray_io.PackedWriter().putf('I', xray.flags if xray is not None else 0)
    )


def export_meshes(chunked_writer, bpy_obj, context):
    mesh_writers = []
    armatures = set()
    materials = set()
    uv_maps_names = {}
    bpy_root = bpy_obj

    def scan_r(bpy_obj):
        if utils.is_helper_object(bpy_obj):
            return
        if bpy_obj.type == 'MESH':
            mesh_writer = xray_io.ChunkedWriter()
            used_material_names = mesh.export_mesh(
                bpy_obj,
                bpy_root,
                mesh_writer,
                context
            )
            mesh_writers.append(mesh_writer)
            for modifier in bpy_obj.modifiers:
                if (modifier.type == 'ARMATURE') and modifier.object:
                    armatures.add(modifier.object)
            for material in bpy_obj.data.materials:
                if not material:
                    continue
                if material.name in used_material_names:
                    materials.add(material)
                    uv_layers = bpy_obj.data.uv_layers
                    if len(uv_layers) > 1:
                        raise utils.AppError(
                            'Object "{}" has more than one UV-map'.format(bpy_obj.name)
                        )
                    uv_maps_names[material.name] = uv_layers[0].name
        elif bpy_obj.type == 'ARMATURE':
            armatures.add(bpy_obj)
        for child in bpy_obj.children:
            scan_r(child)

    scan_r(bpy_obj)
    if len(armatures) > 1:
        raise utils.AppError(
            'Root object "{}" has more than one armature'.format(bpy_obj.name)
        )
    if not mesh_writers:
        raise utils.AppError(
            'Root object "{}" has no meshes'.format(bpy_obj.name)
        )
    if len(mesh_writers) > 1 and len(armatures):
        raise utils.AppError(
            'Skeletal object "{}" has more than one mesh'.format(bpy_obj.name)
        )

    bone_writers = []
    root_bones = []
    armatures = list(armatures)
    if armatures:
        bpy_arm_obj = armatures[0]
        bonemap = {}
        for bone_ in bpy_arm_obj.data.bones:
            if not utils.is_exportable_bone(bone_):
                continue
            real_parent = utils.find_bone_exportable_parent(bone_)
            if not real_parent:
                root_bones.append(bone_.name)
            bone.export_bone(
                bpy_arm_obj, bpy_root, bone_, bone_writers, bonemap, context
            )

        invalid_bones = []
        has_bone_groups = False
        if len(bpy_arm_obj.pose.bone_groups):
            for bone_ in bpy_arm_obj.pose.bones:
                xray = bpy_arm_obj.data.bones[bone_.name].xray
                if xray.exportable:
                    if bone_.bone_group is None:
                        invalid_bones.append(bone_.name)
                    else:
                        has_bone_groups = True
        if invalid_bones and has_bone_groups:
            log.warn(
                'Invalid bone parts: not all bones are tied to the Bone Part',
                data=invalid_bones
            )
    if len(root_bones) > 1:
        raise utils.AppError(
            'Invalid armature object "{}". Has more than one parent: {}'.format(
                bpy_arm_obj.name, root_bones
        ))

    msw = xray_io.ChunkedWriter()
    idx = 0
    for mesh_writer in mesh_writers:
        msw.put(idx, mesh_writer)
        idx += 1

    chunked_writer.put(fmt.Chunks.Object.MESHES, msw)

    arm_list = list(armatures)

    # take care of static objects
    some_arm = arm_list[0] if arm_list else None

    return materials, bone_writers, some_arm, bpy_root, uv_maps_names


def export_surfaces(chunked_writer, context, materials, uv_map_names):
    sfw = xray_io.PackedWriter()
    sfw.putf('I', len(materials))
    for material in materials:
        sfw.puts(material.name)
        if hasattr(material, 'xray'):
            sfw.puts(
                material.xray.eshader
            ).puts(
                material.xray.cshader
            ).puts(
                material.xray.gamemtl
            )
        else:
            sfw.puts('').puts('').puts('')
        tx_name = ''
        if IS_28:
            if material.use_nodes:
                tex_nodes = []
                for node in material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE':
                        tex_nodes.append(node)
                    if len(tex_nodes) == 1:
                        tex_node = tex_nodes[0]
                        if tex_node.image:
                            if context.texname_from_path:
                                tx_name = utils.gen_texture_name(
                                    tex_node, context.textures_folder
                                )
                            else:
                                tx_name = tex_node.name
                    elif len(tex_nodes) > 1:
                        raise utils.AppError(
                            'Material "{}" has more than one texture.'.format(
                                material.name
                        ))
        else:
            if material.active_texture:
                if context.texname_from_path:
                    tx_name = utils.gen_texture_name(
                        material.active_texture, context.textures_folder
                    )
                else:
                    tx_name = material.active_texture.name
        sfw.puts(tx_name)
        if IS_28:
            sfw.puts(uv_map_names[material.name])
        else:
            slot = material.texture_slots[material.active_texture_index]
            sfw.puts(slot.uv_layer if slot else '')
        if hasattr(material, 'xray'):
            sfw.putf('I', material.xray.flags)
        else:
            sfw.putf('I', 0)
        sfw.putf('I', 0x112).putf('I', 1)
    chunked_writer.put(fmt.Chunks.Object.SURFACES2, sfw)


def export_bones(chunked_writer, bone_writers):
    if bone_writers:
        writer = xray_io.ChunkedWriter()
        idx = 0
        for bone_writer in bone_writers:
            writer.put(idx, bone_writer)
            idx += 1
        chunked_writer.put(fmt.Chunks.Object.BONES1, writer)


def export_user_data(chunked_writer, xray):
    if xray.userdata:
        chunked_writer.put(
            fmt.Chunks.Object.USERDATA,
            xray_io.PackedWriter().puts(
                '\r\n'.join(xray.userdata.splitlines())
            )
        )


def export_loddef(chunked_writer, xray):
    if xray.lodref:
        chunked_writer.put(
            fmt.Chunks.Object.LOD_REF,
            xray_io.PackedWriter().puts(xray.lodref)
        )


def export_motions(chunked_writer, some_arm, context, bpy_obj):
    if some_arm and context.export_motions:
        motions = [motion.name for motion in bpy_obj.xray.motions_collection]
        motions = set(motions)
        motions = list(motions)
        motions.sort()
        acts = []
        for act_name in motions:
            act = bpy.data.actions.get(act_name, None)
            if act:
                acts.append(act)
            else:
                log.warn(
                    'Cannot find action "{0}" in object "{1}"'.format(
                        act_name, bpy_obj.name
                    ),
                )
        writer = xray_io.PackedWriter()
        xray_motions.export_motions(writer, acts, some_arm)
        if writer.data:
            chunked_writer.put(fmt.Chunks.Object.MOTIONS, writer)


def export_partitions(chunked_writer, some_arm):
    if some_arm and some_arm.pose.bone_groups:
        exportable_bones = tuple(
            bone_
            for bone_ in some_arm.pose.bones
            if utils.is_exportable_bone(some_arm.data.bones[bone_.name])
        )
        all_groups = (
            (group.name, tuple(
                bone_.name
                for bone_ in exportable_bones
                if bone_.bone_group == group
            ))
            for group in some_arm.pose.bone_groups
        )
        non_empty_groups = tuple(
            group
            for group in all_groups
            if group[1]
        )
        if non_empty_groups:
            writer = xray_io.PackedWriter()
            writer.putf('I', len(non_empty_groups))
            for name, bones in non_empty_groups:
                writer.puts(name)
                writer.putf('I', len(bones))
                for bone_ in bones:
                    writer.puts(bone_)
            chunked_writer.put(fmt.Chunks.Object.PARTITIONS1, writer)


def export_motion_refs(chunked_writer, xray, context):
    motionrefs = xray.motionrefs_collection
    if motionrefs:
        if xray.motionrefs:
            log.warn('MotionRefs: skipped legacy data', data=xray.motionrefs)
        if context.soc_sgroups:
            refs = ','.join(ref.name for ref in motionrefs)
            chunked_writer.put(
                fmt.Chunks.Object.MOTION_REFS,
                xray_io.PackedWriter().puts(refs)
            )
        else:
            writer = xray_io.PackedWriter()
            writer.putf('I', len(motionrefs))
            for ref in motionrefs:
                writer.puts(ref.name)
            chunked_writer.put(fmt.Chunks.Object.SMOTIONS3, writer)
    elif xray.motionrefs:
        chunked_writer.put(
            fmt.Chunks.Object.MOTION_REFS,
            xray_io.PackedWriter().puts(xray.motionrefs)
        )


def export_transform(chunked_writer, bpy_root):
    root_matrix = bpy_root.matrix_world
    if root_matrix != mathutils.Matrix.Identity(4):
        writer = xray_io.PackedWriter()
        writer.putf('fff', *pw_v3f(root_matrix.to_translation()))
        writer.putf('fff', *pw_v3f(root_matrix.to_euler('YXZ')))
        chunked_writer.put(fmt.Chunks.Object.TRANSFORM, writer)


def export_revision(chunked_writer, xray):
    curruser = '\\\\{}\\{}'.format(platform.node(), getpass.getuser())
    currtime = int(time.time())
    writer = xray_io.PackedWriter()
    if (not xray.revision.owner) or (xray.revision.owner == curruser):
        writer.puts(curruser)
        writer.putf(
            'i', xray.revision.ctime if xray.revision.ctime else currtime
        )
        writer.puts('')
        writer.putf('i', 0)
    else:
        writer.puts(xray.revision.owner)
        writer.putf('I', xray.revision.ctime)
        writer.puts(curruser)
        writer.putf('I', currtime)
    chunked_writer.put(fmt.Chunks.Object.REVISION, writer)


def export_main(bpy_obj, chunked_writer, context):
    xray = bpy_obj.xray if hasattr(bpy_obj, 'xray') else None

    export_version(chunked_writer)
    export_flags(chunked_writer, xray)
    materials, bone_writers, some_arm, bpy_root, uv_map_names = export_meshes(
        chunked_writer, bpy_obj, context
    )
    export_surfaces(chunked_writer, context, materials, uv_map_names)
    export_bones(chunked_writer, bone_writers)
    export_user_data(chunked_writer, xray)
    export_loddef(chunked_writer, xray)
    export_motions(chunked_writer, some_arm, context, bpy_obj)
    export_partitions(chunked_writer, some_arm)
    export_motion_refs(chunked_writer, xray, context)
    export_transform(chunked_writer, bpy_root)
    export_revision(chunked_writer, xray)
