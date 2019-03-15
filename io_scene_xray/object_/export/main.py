
import platform
import getpass
import time

import bpy
import mathutils

from ... import xray_io
from ... import utils
from ... import log
from ... import xray_motions
from .. import format_
from . import mesh
from . import bone


def pw_v3f(vec):
    return vec[0], vec[2], vec[1]


def export_main(bpy_obj, chunked_writer, context):
    chunked_writer.put(format_.Chunks.Object.VERSION, xray_io.PackedWriter().putf('H', 0x10))
    xray = bpy_obj.xray if hasattr(bpy_obj, 'xray') else None
    chunked_writer.put(
        format_.Chunks.Object.FLAGS,
        xray_io.PackedWriter().putf('I', xray.flags if xray is not None else 0)
    )
    mesh_writers = []
    armatures = set()
    materials = set()
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
        elif bpy_obj.type == 'ARMATURE':
            armatures.add(bpy_obj)
        for child in bpy_obj.children:
            scan_r(child)

    scan_r(bpy_obj)

    bone_writers = []
    for bpy_arm_obj in armatures:
        bonemap = {}
        for bone_ in bpy_arm_obj.data.bones:
            if not utils.is_exportable_bone(bone_):
                continue
            bone.export_bone(bpy_arm_obj, bpy_root, bone_, bone_writers, bonemap, context)

    msw = xray_io.ChunkedWriter()
    idx = 0
    for mesh_writer in mesh_writers:
        msw.put(idx, mesh_writer)
        idx += 1

    chunked_writer.put(format_.Chunks.Object.MESHES, msw)
    sfw = xray_io.PackedWriter()
    sfw.putf('I', len(materials))
    for material in materials:
        sfw.puts(material.name)
        if hasattr(material, 'xray'):
            sfw.puts(material.xray.eshader).puts(material.xray.cshader).puts(material.xray.gamemtl)
        else:
            sfw.puts('').puts('').puts('')
        tx_name = ''
        if material.active_texture:
            if context.texname_from_path:
                tx_name = utils.gen_texture_name(material.active_texture, context.textures_folder)
            else:
                tx_name = material.active_texture.name
        sfw.puts(tx_name)
        slot = material.texture_slots[material.active_texture_index]
        sfw.puts(slot.uv_layer if slot else '')
        if hasattr(material, 'xray'):
            sfw.putf('I', material.xray.flags)
        else:
            sfw.putf('I', 0)
        sfw.putf('I', 0x112).putf('I', 1)
    chunked_writer.put(format_.Chunks.Object.SURFACES2, sfw)

    if bone_writers:
        writer = xray_io.ChunkedWriter()
        idx = 0
        for bone_writer in bone_writers:
            writer.put(idx, bone_writer)
            idx += 1
        chunked_writer.put(format_.Chunks.Object.BONES1, writer)

    if xray.userdata:
        chunked_writer.put(
            format_.Chunks.Object.USERDATA,
            xray_io.PackedWriter().puts('\r\n'.join(xray.userdata.splitlines()))
        )
    if xray.lodref:
        chunked_writer.put(format_.Chunks.Object.LOD_REF, xray_io.PackedWriter().puts(xray.lodref))

    arm_list = list(armatures)
    some_arm = arm_list[0] if arm_list else None  # take care of static objects

    if some_arm and context.export_motions:
        acts = [motion.name for motion in bpy_obj.xray.motions_collection]
        acts = set(acts)
        acts = list(acts)
        acts.sort()
        acts = [bpy.data.actions[name] for name in acts]
        writer = xray_io.PackedWriter()
        xray_motions.export_motions(writer, acts, some_arm)
        if writer.data:
            chunked_writer.put(format_.Chunks.Object.MOTIONS, writer)

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
            chunked_writer.put(format_.Chunks.Object.PARTITIONS1, writer)

    motionrefs = xray.motionrefs_collection
    if motionrefs:
        if xray.motionrefs:
            log.warn('MotionRefs: skipped legacy data', data=xray.motionrefs)
        if context.soc_sgroups:
            refs = ','.join(ref.name for ref in motionrefs)
            chunked_writer.put(format_.Chunks.Object.MOTION_REFS, xray_io.PackedWriter().puts(refs))
        else:
            writer = xray_io.PackedWriter()
            writer.putf('I', len(motionrefs))
            for ref in motionrefs:
                writer.puts(ref.name)
            chunked_writer.put(format_.Chunks.Object.SMOTIONS3, writer)
    elif xray.motionrefs:
        chunked_writer.put(format_.Chunks.Object.MOTION_REFS, xray_io.PackedWriter().puts(xray.motionrefs))

    root_matrix = bpy_root.matrix_world
    if root_matrix != mathutils.Matrix.Identity(4):
        writer = xray_io.PackedWriter()
        writer.putf('fff', *pw_v3f(root_matrix.to_translation()))
        writer.putf('fff', *pw_v3f(root_matrix.to_euler('YXZ')))
        chunked_writer.put(format_.Chunks.Object.TRANSFORM, writer)

    curruser = '\\\\{}\\{}'.format(platform.node(), getpass.getuser())
    currtime = int(time.time())
    writer = xray_io.PackedWriter()
    if (not xray.revision.owner) or (xray.revision.owner == curruser):
        writer.puts(curruser)
        writer.putf('I', xray.revision.ctime if xray.revision.ctime else currtime)
        writer.puts('')
        writer.putf('I', 0)
    else:
        writer.puts(xray.revision.owner)
        writer.putf('I', xray.revision.ctime)
        writer.puts(curruser)
        writer.putf('I', currtime)
    chunked_writer.put(format_.Chunks.Object.REVISION, writer)
