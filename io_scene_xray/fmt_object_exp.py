import io

import bmesh
import bpy
import mathutils

from .xray_io import ChunkedWriter, PackedWriter
from .xray_motions import export_motions, MATRIX_BONE_INVERTED
from .fmt_object import Chunks
from .utils import is_exportable_bone, find_bone_exportable_parent, AppError, \
    convert_object_to_space_bmesh, calculate_mesh_bbox, gen_texture_name, is_helper_object
from .utils import BAD_VTX_GROUP_NAME
from . import log


class ExportContext:
    def __init__(self, textures_folder, export_motions, soc_sgroups, texname_from_path):
        self.textures_folder = textures_folder
        self.export_motions = export_motions
        self.soc_sgroups = soc_sgroups
        self.texname_from_path = texname_from_path


def pw_v3f(vec):
    return vec[0], vec[2], vec[1]


def _export_sg_soc(bmfaces):
    face_sgroup = dict()

    def mark_fsg(face, sgroup):
        faces = [face]
        for face in faces:
            for edge in face.edges:
                if not edge.smooth:
                    continue
                for linked_face in edge.link_faces:
                    if face_sgroup.get(linked_face) is None:
                        face_sgroup[linked_face] = sgroup
                        faces.append(linked_face)

    sgroup_gen = 0
    for face in bmfaces:
        sgroup = face_sgroup.get(face)
        if sgroup is None:
            face_sgroup[face] = sgroup = sgroup_gen
            sgroup_gen += 1
            mark_fsg(face, sgroup)
        yield sgroup


def _check_sg_soc(bmedges, sgroups):
    for edge in bmedges:
        if len(edge.link_faces) != 2:
            continue
        sg0, sg1 = sgroups[edge.link_faces[0].index], sgroups[edge.link_faces[1].index]
        if edge.smooth:
            if sg0 != sg1:
                return 'Maya-SG incompatible: smooth edge adjacents has different smoothing group'
        else:
            if sg0 == sg1:
                return 'Maya-SG incompatible: sharp edge adjacents has same smoothing group'


def _export_sg_new(bmfaces):
    for face in bmfaces:
        sm_group = 0
        for eidx, edge in enumerate(face.edges):
            if not edge.smooth:
                sm_group |= (4, 2, 1)[eidx]
        yield sm_group


@log.with_context('export-mesh')
def _export_mesh(bpy_obj, bpy_root, cw, context):
    log.update(mesh=bpy_obj.data.name)
    cw.put(Chunks.Mesh.VERSION, PackedWriter().putf('H', 0x11))
    mesh_name = bpy_obj.data.name if bpy_obj == bpy_root else bpy_obj.name
    cw.put(Chunks.Mesh.MESHNAME, PackedWriter().puts(mesh_name))

    bm = convert_object_to_space_bmesh(bpy_obj, bpy_root.matrix_world)
    bml = bm.verts.layers.deform.verify()
    bad_vgroups = [vertex_group.name.startswith(BAD_VTX_GROUP_NAME) for vertex_group in bpy_obj.vertex_groups]
    bad_verts = [vertex for vertex in bm.verts if any(bad_vgroups[k] for k in vertex[bml].keys())]
    if bad_verts:
        log.warn('skipping geometry from "{}"-s vertex groups'.format(BAD_VTX_GROUP_NAME))
        bmesh.ops.delete(bm, geom=bad_verts, context=1)

    bbox = calculate_mesh_bbox(bm.verts)
    cw.put(
        Chunks.Mesh.BBOX,
        PackedWriter().putf('fff', *pw_v3f(bbox[0])).putf('fff', *pw_v3f(bbox[1]))
    )
    if hasattr(bpy_obj.data, 'xray'):
        flags = bpy_obj.data.xray.flags & ~Chunks.Mesh.Flags.SG_MASK  # MAX sg-format currently unsupported (we use Maya sg-format)
        cw.put(Chunks.Mesh.FLAGS, PackedWriter().putf('B', flags))
    else:
        cw.put(Chunks.Mesh.FLAGS, PackedWriter().putf('B', 1))

    bmesh.ops.triangulate(bm, faces=bm.faces)

    writer = PackedWriter()
    writer.putf('I', len(bm.verts))
    for vertex in bm.verts:
        writer.putf('fff', *pw_v3f(vertex.co))
    cw.put(Chunks.Mesh.VERTS, writer)

    uvs = []
    vtx = []
    fcs = []
    uv_layer = bm.loops.layers.uv.active
    if not uv_layer:
        raise AppError('UV-map is required, but not found')

    writer = PackedWriter()
    writer.putf('I', len(bm.faces))
    for fidx in bm.faces:
        for i in (0, 2, 1):
            writer.putf('II', fidx.verts[i].index, len(uvs))
            uvc = fidx.loops[i][uv_layer].uv
            uvs.append((uvc[0], 1 - uvc[1]))
            vtx.append(fidx.verts[i].index)
            fcs.append(fidx.index)
    cw.put(Chunks.Mesh.FACES, writer)

    wmaps = []
    wmaps_cnt = 0
    for vertex_group, bad in zip(bpy_obj.vertex_groups, bad_vgroups):
        if bad:
            wmaps.append(None)
            continue
        wmaps.append(([], wmaps_cnt))
        wmaps_cnt += 1

    wrefs = []
    for vidx, vertex in enumerate(bm.verts):
        wr = []
        wrefs.append(wr)
        vw = vertex[bml]
        for vgi in vw.keys():
            wmap = wmaps[vgi]
            if wmap is None:
                continue
            wr.append((1 + wmap[1], len(wmap[0])))
            wmap[0].append(vidx)

    writer = PackedWriter()
    writer.putf('I', len(uvs))
    for i in range(len(uvs)):
        vidx = vtx[i]
        wref = wrefs[vidx]
        writer.putf('B', 1 + len(wref)).putf('II', 0, i)
        for ref in wref:
            writer.putf('II', *ref)
    cw.put(Chunks.Mesh.VMREFS, writer)

    writer = PackedWriter()
    sfaces = {
        m.name if m else None: [fidx for fidx, face in enumerate(bm.faces) if face.material_index == mi]
        for mi, m in enumerate(bpy_obj.data.materials)
    }

    used_material_names = set()
    for material_name, faces_indices in sfaces.items():
        if faces_indices:
            used_material_names.add(material_name)

    if not sfaces:
        raise AppError('mesh has no material')
    writer.putf('H', len(used_material_names))
    for name, fidxs in sfaces.items():
        if name in used_material_names:
            writer.puts(name).putf('I', len(fidxs))
            for fidx in fidxs:
                writer.putf('I', fidx)
    cw.put(Chunks.Mesh.SFACE, writer)

    writer = PackedWriter()
    sgroups = []
    if context.soc_sgroups:
        sgroups = tuple(_export_sg_soc(bm.faces))
        err = _check_sg_soc(bm.edges, sgroups)  # check for Maya compatibility
        if err:
            log.warn(err)
    else:
        sgroups = _export_sg_new(bm.faces)
    for sgroup in sgroups:
        writer.putf('I', sgroup)
    cw.put(Chunks.Mesh.SG, writer)

    writer = PackedWriter()
    writer.putf('I', 1 + wmaps_cnt)
    texture = bpy_obj.data.uv_textures.active
    writer.puts(texture.name).putf('B', 2).putf('B', 1).putf('B', 0)
    writer.putf('I', len(uvs))
    for uvc in uvs:
        writer.putf('ff', *uvc)
    for vidx in vtx:
        writer.putf('I', vidx)
    for fidx in fcs:
        writer.putf('I', fidx)
    for vgi, vertex_group in enumerate(bpy_obj.vertex_groups):
        wmap = wmaps[vgi]
        if wmap is None:
            continue
        vtx = wmap[0]
        writer.puts(vertex_group.name)
        writer.putf('B', 1).putf('B', 0).putf('B', 1)
        writer.putf('I', len(vtx))
        for vidx in vtx:
            writer.putf('f', bm.verts[vidx][bml][vgi])
        writer.putf(str(len(vtx)) + 'I', *vtx)
    cw.put(Chunks.Mesh.VMAPS2, writer)
    return used_material_names


def _export_bone(bpy_arm_obj, bpy_root, bpy_bone, writers, bonemap, context):
    real_parent = find_bone_exportable_parent(bpy_bone)
    if real_parent:
        if bonemap.get(real_parent) is None:
            _export_bone(bpy_arm_obj, bpy_root, real_parent, writers, bonemap, context)

    xray = bpy_bone.xray
    writer = ChunkedWriter()
    writers.append(writer)
    bonemap[bpy_bone] = writer
    writer.put(Chunks.Bone.VERSION, PackedWriter().putf('H', 0x02))
    writer.put(Chunks.Bone.DEF, PackedWriter()
               .puts(bpy_bone.name)
               .puts(real_parent.name if real_parent else '')
               .puts(bpy_bone.name))  # vmap
    xmat = bpy_root.matrix_world.inverted() * bpy_arm_obj.matrix_world
    mat = xmat * bpy_bone.matrix_local * MATRIX_BONE_INVERTED
    if real_parent:
        mat = (xmat * real_parent.matrix_local * MATRIX_BONE_INVERTED).inverted() * mat
    eul = mat.to_euler('YXZ')
    writer.put(Chunks.Bone.BIND_POSE, PackedWriter()
               .putf('fff', *pw_v3f(mat.to_translation()))
               .putf('fff', -eul.x, -eul.z, -eul.y)
               .putf('f', xray.length))
    writer.put(Chunks.Bone.MATERIAL, PackedWriter().puts(xray.gamemtl))
    verdif = xray.shape.check_version_different()
    if verdif != 0:
        log.warn(
            'bone edited with a different version of this plugin',
            bone=bpy_bone.name,
            version=xray.shape.fmt_version_different(verdif)
        )
    writer.put(Chunks.Bone.SHAPE, PackedWriter()
               .putf('H', int(xray.shape.type))
               .putf('H', xray.shape.flags)
               .putf('fffffffff', *xray.shape.box_rot)
               .putf('fff', *xray.shape.box_trn)
               .putf('fff', *xray.shape.box_hsz)
               .putf('fff', *xray.shape.sph_pos)
               .putf('f', xray.shape.sph_rad)
               .putf('fff', *xray.shape.cyl_pos)
               .putf('fff', *xray.shape.cyl_dir)
               .putf('f', xray.shape.cyl_hgh)
               .putf('f', xray.shape.cyl_rad))
    pose_bone = bpy_arm_obj.pose.bones[bpy_bone.name]
    writer.put(Chunks.Bone.IK_JOINT, PackedWriter()
               .putf('I', int(xray.ikjoint.type))
               .putf('ff', pose_bone.ik_min_x, pose_bone.ik_max_x)
               .putf('ff', xray.ikjoint.lim_x_spr, xray.ikjoint.lim_x_dmp)
               .putf('ff', pose_bone.ik_min_y, pose_bone.ik_max_y)
               .putf('ff', xray.ikjoint.lim_y_spr, xray.ikjoint.lim_y_dmp)
               .putf('ff', pose_bone.ik_min_z, pose_bone.ik_max_z)
               .putf('ff', xray.ikjoint.lim_z_spr, xray.ikjoint.lim_z_dmp)
               .putf('ff', xray.ikjoint.spring, xray.ikjoint.damping))
    if xray.ikflags:
        writer.put(Chunks.Bone.IK_FLAGS, PackedWriter().putf('I', xray.ikflags))
        if xray.ikflags_breakable:
            writer.put(Chunks.Bone.BREAK_PARAMS, PackedWriter()
                       .putf('f', xray.breakf.force)
                       .putf('f', xray.breakf.torque))
    if int(xray.ikjoint.type) and xray.friction:
        writer.put(Chunks.Bone.FRICTION, PackedWriter()
                   .putf('f', xray.friction))
    if xray.mass.value:
        writer.put(Chunks.Bone.MASS_PARAMS, PackedWriter()
                   .putf('f', xray.mass.value)
                   .putf('fff', *pw_v3f(xray.mass.center)))


def _export_main(bpy_obj, chunked_writer, context):
    chunked_writer.put(Chunks.Object.VERSION, PackedWriter().putf('H', 0x10))
    xray = bpy_obj.xray if hasattr(bpy_obj, 'xray') else None
    chunked_writer.put(
        Chunks.Object.FLAGS,
        PackedWriter().putf('I', xray.flags if xray is not None else 0)
    )
    mesh_writers = []
    armatures = set()
    materials = set()
    bpy_root = bpy_obj

    def scan_r(bpy_obj):
        if is_helper_object(bpy_obj):
            return
        if bpy_obj.type == 'MESH':
            mesh_writer = ChunkedWriter()
            used_material_names = _export_mesh(
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
        for bone in bpy_arm_obj.data.bones:
            if not is_exportable_bone(bone):
                continue
            _export_bone(bpy_arm_obj, bpy_root, bone, bone_writers, bonemap, context)

    msw = ChunkedWriter()
    idx = 0
    for mesh_writer in mesh_writers:
        msw.put(idx, mesh_writer)
        idx += 1

    chunked_writer.put(Chunks.Object.MESHES, msw)
    sfw = PackedWriter()
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
                tx_name = gen_texture_name(material.active_texture, context.textures_folder)
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
    chunked_writer.put(Chunks.Object.SURFACES2, sfw)

    if bone_writers:
        writer = ChunkedWriter()
        idx = 0
        for bone_writer in bone_writers:
            writer.put(idx, bone_writer)
            idx += 1
        chunked_writer.put(Chunks.Object.BONES1, writer)

    if xray.userdata:
        chunked_writer.put(
            Chunks.Object.USERDATA,
            PackedWriter().puts('\r\n'.join(xray.userdata.splitlines()))
        )
    if xray.lodref:
        chunked_writer.put(Chunks.Object.LOD_REF, PackedWriter().puts(xray.lodref))

    arm_list = list(armatures)
    some_arm = arm_list[0] if arm_list else None  # take care of static objects

    if some_arm and context.export_motions:
        acts = [motion.name for motion in bpy_obj.xray.motions_collection]
        acts = set(acts)
        acts = list(acts)
        acts.sort()
        acts = [bpy.data.actions[name] for name in acts]
        writer = PackedWriter()
        export_motions(writer, acts, some_arm)
        if writer.data:
            chunked_writer.put(Chunks.Object.MOTIONS, writer)

    if some_arm and some_arm.pose.bone_groups:
        exportable_bones = tuple(
            bone
            for bone in some_arm.pose.bones
            if is_exportable_bone(some_arm.data.bones[bone.name])
        )
        all_groups = (
            (group.name, tuple(
                bone.name
                for bone in exportable_bones
                if bone.bone_group == group
            ))
            for group in some_arm.pose.bone_groups
        )
        non_empty_groups = tuple(
            group
            for group in all_groups
            if group[1]
        )
        if non_empty_groups:
            writer = PackedWriter()
            writer.putf('I', len(non_empty_groups))
            for name, bones in non_empty_groups:
                writer.puts(name)
                writer.putf('I', len(bones))
                for bone in bones:
                    writer.puts(bone)
            chunked_writer.put(Chunks.Object.PARTITIONS1, writer)

    motionrefs = xray.motionrefs_collection
    if motionrefs:
        if xray.motionrefs:
            log.warn('MotionRefs: skipped legacy data', data=xray.motionrefs)
        if context.soc_sgroups:
            refs = ','.join(ref.name for ref in motionrefs)
            chunked_writer.put(Chunks.Object.MOTION_REFS, PackedWriter().puts(refs))
        else:
            writer = PackedWriter()
            writer.putf('I', len(motionrefs))
            for ref in motionrefs:
                writer.puts(ref.name)
            chunked_writer.put(Chunks.Object.SMOTIONS3, writer)
    elif xray.motionrefs:
        chunked_writer.put(Chunks.Object.MOTION_REFS, PackedWriter().puts(xray.motionrefs))

    root_matrix = bpy_root.matrix_world
    if root_matrix != mathutils.Matrix.Identity(4):
        writer = PackedWriter()
        writer.putf('fff', *pw_v3f(root_matrix.to_translation()))
        writer.putf('fff', *pw_v3f(root_matrix.to_euler('YXZ')))
        chunked_writer.put(Chunks.Object.TRANSFORM, writer)

    import platform, getpass, time
    curruser = '\\\\{}\\{}'.format(platform.node(), getpass.getuser())
    currtime = int(time.time())
    writer = PackedWriter()
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
    chunked_writer.put(Chunks.Object.REVISION, writer)


def _export(bpy_obj, chunked_writer, context):
    writer = ChunkedWriter()
    _export_main(bpy_obj, writer, context)
    chunked_writer.put(Chunks.Object.MAIN, writer)


def export_file(bpy_obj, fpath, context):
    with io.open(fpath, 'wb') as file:
        writer = ChunkedWriter()
        _export(bpy_obj, writer, context)
        file.write(writer.data)
