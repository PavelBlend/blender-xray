import bmesh
import bpy
import mathutils
import io
from .xray_io import ChunkedWriter, PackedWriter
from .fmt_object import Chunks
from .utils import is_fake_bone, find_bone_real_parent, AppError, convert_object_to_worldspace_bmesh, calculate_mesh_bbox


def pw_v3f(v):
    return v[0], v[2], v[1]


def _export_mesh(bpy_obj, cw):
    cw.put(Chunks.Mesh.VERSION, PackedWriter().putf('H', 0x11))
    cw.put(Chunks.Mesh.MESHNAME, PackedWriter().puts(bpy_obj.name))

    bm = convert_object_to_worldspace_bmesh(bpy_obj)

    bbox = calculate_mesh_bbox(bm.verts)
    cw.put(Chunks.Mesh.BBOX, PackedWriter().putf('fff', *pw_v3f(bbox[0])).putf('fff', *pw_v3f(bbox[1])))
    if hasattr(bpy_obj.data, 'xray'):
        cw.put(Chunks.Mesh.FLAGS, PackedWriter().putf('B', bpy_obj.data.xray.flags))
    else:
        cw.put(Chunks.Mesh.FLAGS, PackedWriter().putf('B', 1))

    bmesh.ops.triangulate(bm, faces=bm.faces)

    pw = PackedWriter()
    pw.putf('I', len(bm.verts))
    for v in bm.verts:
        pw.putf('fff', *pw_v3f(v.co))
    cw.put(Chunks.Mesh.VERTS, pw)

    uvs = []
    vtx = []
    fcs = []
    uv_layer = bm.loops.layers.uv.active
    if not uv_layer:
        raise AppError('UV-map is required, but not found')

    pw = PackedWriter()
    pw.putf('I', len(bm.faces))
    for f in bm.faces:
        for i in (0, 2, 1):
            pw.putf('II', f.verts[i].index, len(uvs))
            uv = f.loops[i][uv_layer].uv
            uvs.append((uv[0], 1 - uv[1]))
            vtx.append(f.verts[i].index)
            fcs.append(f.index)
    cw.put(Chunks.Mesh.FACES, pw)

    bml = bm.verts.layers.deform.verify()
    wmaps = [[] for _ in bpy_obj.vertex_groups]
    wrefs = []
    for vi, v in enumerate(bm.verts):
        wr = []
        wrefs.append(wr)
        vw = v[bml]
        for vgi in vw.keys():
            wm = wmaps[vgi]
            wr.append((1 + vgi, len(wm)))
            wm.append(vi)

    pw = PackedWriter()
    pw.putf('I', len(uvs))
    for i in range(len(uvs)):
        vi = vtx[i]
        wr = wrefs[vi]
        pw.putf('B', 1 + len(wr)).putf('II', 0, i)
        for r in wr:
            pw.putf('II', *r)
    cw.put(Chunks.Mesh.VMREFS, pw)

    pw = PackedWriter()
    sfaces = {
        m.name: [fi for fi, f in enumerate(bm.faces) if f.material_index == mi]
        for mi, m in enumerate(bpy_obj.data.materials)
    }
    if not sfaces:
        raise AppError('mesh "' + bpy_obj.data.name + '" has no material')
    pw.putf('H', len(sfaces))
    for n, ff in sfaces.items():
        pw.puts(n).putf('I', len(ff))
        for f in ff:
            pw.putf('I', f)
    cw.put(Chunks.Mesh.SFACE, pw)

    def mark_fsg(f, sg):
        ff = [f]
        for f in ff:
            for e in f.edges:
                if not e.smooth:
                    continue
                for lf in e.link_faces:
                    if fsg.get(lf) is None:
                        fsg[lf] = sg
                        ff.append(lf)
    fsg = {}
    sgg = 0
    pw = PackedWriter()
    for f in bm.faces:
        sg = fsg.get(f)
        if sg is None:
            fsg[f] = sg = sgg
            sgg += 1
            mark_fsg(f, sg)
        pw.putf('I', sg)
    cw.put(Chunks.Mesh.SG, pw)

    pw = PackedWriter()
    pw.putf('I', 1 + len(wmaps))
    at = bpy_obj.data.uv_textures.active
    pw.puts(at.name).putf('B', 2).putf('B', 1).putf('B', 0)
    pw.putf('I', len(uvs))
    for uv in uvs:
        pw.putf('ff', *uv)
    for vi in vtx:
        pw.putf('I', vi)
    for fi in fcs:
        pw.putf('I', fi)
    for vgi, vg in enumerate(bpy_obj.vertex_groups):
        pw.puts(bpy_obj.vertex_groups[vgi].name)
        pw.putf('B', 1).putf('B', 0).putf('B', 1)
        vtx = wmaps[vgi]
        pw.putf('I', len(vtx))
        for vi in vtx:
            pw.putf('f', bm.verts[vi][bml][vgi])
        pw.putf(str(len(vtx)) + 'I', *vtx)
    cw.put(Chunks.Mesh.VMAPS2, pw)


__matrix_bone = mathutils.Matrix(((1.0, 0.0, 0.0, 0.0), (0.0, 0.0, -1.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
__matrix_bone_inv = __matrix_bone.inverted()


def _export_bone(bpy_arm_obj, bpy_bone, writers, bonemap):
    real_parent = find_bone_real_parent(bpy_bone)
    if real_parent:
        if bonemap.get(real_parent) is None:
            _export_bone(bpy_arm_obj, real_parent, bonemap)

    xr = bpy_bone.xray
    cw = ChunkedWriter()
    writers.append(cw)
    bonemap[bpy_bone] = cw
    cw.put(Chunks.Bone.VERSION, PackedWriter().putf('H', 0x02))
    cw.put(Chunks.Bone.DEF, PackedWriter()
           .puts(bpy_bone.name)
           .puts(real_parent.name if real_parent else '')
           .puts(bpy_bone.name))  # vmap
    mw = bpy_arm_obj.matrix_world
    tm = mw * bpy_bone.matrix_local * __matrix_bone_inv
    if real_parent:
        tm = (mw * real_parent.matrix_local * __matrix_bone_inv).inverted() * tm
    e = tm.to_euler('YXZ')
    cw.put(Chunks.Bone.BIND_POSE, PackedWriter()
           .putf('fff', *pw_v3f(tm.to_translation()))
           .putf('fff', -e.x, -e.z, -e.y)
           .putf('f', xr.length))
    cw.put(Chunks.Bone.MATERIAL, PackedWriter().puts(xr.gamemtl))
    cw.put(Chunks.Bone.SHAPE, PackedWriter()
           .putf('H', int(xr.shape.type))
           .putf('H', xr.shape.flags)
           .putf('fffffffff', *xr.shape.box_rot)
           .putf('fff', *xr.shape.box_trn)
           .putf('fff', *xr.shape.box_hsz)
           .putf('fff', *xr.shape.sph_pos)
           .putf('f', xr.shape.sph_rad)
           .putf('fff', *xr.shape.cyl_pos)
           .putf('fff', *xr.shape.cyl_dir)
           .putf('f', xr.shape.cyl_hgh)
           .putf('f', xr.shape.cyl_rad))
    bp = bpy_arm_obj.pose.bones[bpy_bone.name]
    cw.put(Chunks.Bone.IK_JOINT, PackedWriter()
           .putf('I', int(xr.ikjoint.type))
           .putf('ff', bp.ik_min_x, bp.ik_max_x)
           .putf('ff', xr.ikjoint.lim_x_spr, xr.ikjoint.lim_x_dmp)
           .putf('ff', bp.ik_min_y, bp.ik_max_y)
           .putf('ff', xr.ikjoint.lim_y_spr, xr.ikjoint.lim_y_dmp)
           .putf('ff', bp.ik_min_z, bp.ik_max_z)
           .putf('ff', xr.ikjoint.lim_z_spr, xr.ikjoint.lim_z_dmp)
           .putf('ff', xr.ikjoint.spring, xr.ikjoint.damping))
    if xr.ikflags:
        cw.put(Chunks.Bone.IK_FLAGS, PackedWriter().putf('I', xr.ikflags))
        if xr.ikflags_breakable:
            cw.put(Chunks.Bone.BREAK_PARAMS, PackedWriter()
                   .putf('f', xr.breakf.force)
                   .putf('f', xr.breakf.torque))
    if int(xr.ikjoint.type) and xr.friction:
        cw.put(Chunks.Bone.FRICTION, PackedWriter()
               .putf('f', xr.friction))
    if xr.mass.value:
        cw.put(Chunks.Bone.MASS_PARAMS, PackedWriter()
               .putf('f', xr.mass.value)
               .putf('fff', *pw_v3f(xr.mass.center)))


def _export_main(bpy_obj, cw):
    cw.put(Chunks.Object.VERSION, PackedWriter().putf('H', 0x10))
    xr = bpy_obj.xray if hasattr(bpy_obj, 'xray') else None
    cw.put(Chunks.Object.FLAGS, PackedWriter().putf('I', xr.flags if xr is not None else 0))
    meshes = []
    armatures = set()
    materials = set()

    def scan_r(bpy_obj):
        if bpy_obj.type == 'MESH':
            mw = ChunkedWriter()
            _export_mesh(bpy_obj, mw)
            meshes.append(mw)
            for m in bpy_obj.modifiers:
                if (m.type == 'ARMATURE') and m.object:
                    armatures.add(m.object)
            for m in bpy_obj.data.materials:
                materials.add(m)
        elif bpy_obj.type == 'ARMATURE':
            armatures.add(bpy_obj)
        for c in bpy_obj.children:
            scan_r(c)

    scan_r(bpy_obj)

    bones = []
    msw = ChunkedWriter()
    idx = 0
    for bpy_arm_obj in armatures:
        bonemap = {}
        for b in bpy_arm_obj.data.bones:
            if is_fake_bone(b):
                continue
            _export_bone(bpy_arm_obj, b, bones, bonemap)
    for mw in meshes:
        msw.put(idx, mw)
        idx += 1
    cw.put(Chunks.Object.MESHES, msw)
    sfw = PackedWriter()
    sfw.putf('I', len(materials))
    for m in materials:
        sfw.puts(m.name)
        if hasattr(m, 'xray'):
            sfw.puts(m.xray.eshader).puts(m.xray.cshader).puts(m.xray.gamemtl)
        else:
            sfw.puts('').puts('').puts('')
        sfw.puts(m.active_texture.name if m.active_texture else '')
        ts = m.texture_slots[m.active_texture_index]
        sfw.puts(ts.uv_layer if ts else '')
        if hasattr(m, 'xray'):
            sfw.putf('I', m.xray.flags)
        else:
            sfw.putf('I', 0)
        sfw.putf('I', 0x112).putf('I', 1)
    cw.put(Chunks.Object.SURFACES2, sfw)

    if bones:
        bw = ChunkedWriter()
        idx = 0
        for b in bones:
            bw.put(idx, b)
            idx += 1
        cw.put(Chunks.Object.BONES1, bw)

    if xr.userdata:
        cw.put(Chunks.Object.USERDATA, PackedWriter().puts(xr.userdata))
    if xr.lodref:
        cw.put(Chunks.Object.LOD_REF, PackedWriter().puts(xr.lodref))
    if xr.motionrefs:
        cw.put(Chunks.Object.MOTION_REFS, PackedWriter().puts(xr.motionrefs))


def _export(bpy_obj, cw):
    w = ChunkedWriter()
    _export_main(bpy_obj, w)
    cw.put(Chunks.Object.MAIN, w)


def export_file(bpy_obj, fpath):
    with io.open(fpath, 'wb') as f:
        cw = ChunkedWriter()
        _export(bpy_obj, cw)
        f.write(cw.data)
