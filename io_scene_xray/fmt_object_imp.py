import bmesh
import bpy
import io
import math
import mathutils
import os.path
from .xray_io import ChunkedReader, PackedReader
from .fmt_object import Chunks
from .utils import find_bone_real_parent, fix_ensure_lookup_table
from .xray_envelope import Shape


class ImportContext:
    def __init__(self, textures, soc_sgroups, import_motions, report, op, bpy=None):
        from . import bl_info
        from .utils import version_to_number
        self.version = version_to_number(*bl_info['version'])
        self.report = report
        self.bpy = bpy
        self.textures_folder = textures
        self.soc_sgroups = soc_sgroups
        self.import_motions = import_motions
        self.op = op
        self.used_materials = None

    def before_import_file(self):
        self.used_materials = {}

    def image(self, relpath):
        relpath = relpath.lower().replace('\\', os.path.sep)
        filepath = os.path.abspath(os.path.join(self.textures_folder, relpath + '.dds'))
        result = None
        for i in bpy.data.images:
            if bpy.path.abspath(i.filepath) == filepath:
                result = i
                break
        if result is None:
            try:
                result = self.bpy.data.images.load(filepath)
            except RuntimeError as ex:  # e.g. 'Error: Cannot read ...'
                self.report({'WARNING'}, str(ex))
                result = self.bpy.data.images.new(os.path.basename(relpath), 0, 0)
                result.source = 'FILE'
                result.filepath = filepath
        return result


def warn_imknown_chunk(cid, location):
    print('WARNING: UNKNOWN CHUNK: {:#x} IN: {}'.format(cid, location))


def debug(m):
    #print(m)
    pass


def read_v3f(packed_reader):
    v = packed_reader.getf('fff')
    return v[0], v[2], v[1]


def _cop_sgfunc(ga, gb, ea, eb):
    bfa, bfb = bool(ga & 0x8), bool(gb & 0x8)  # test backface-s
    if bfa != bfb:
        return False

    def is_soft(g, bf, e):
        return not (g & (4, 2, 1)[(4 - e) % 3 if bf else e])

    return is_soft(ga, bfa, ea) and is_soft(gb, bfb, eb)


def _import_mesh(cx, cr, parent):
    ver = cr.nextf(Chunks.Mesh.VERSION, 'H')[0]
    if ver != 0x11:
        raise Exception('unsupported MESH format version: {:#x}'.format(ver))
    bm_data = bpy.data.meshes.new(name='tmp.mesh')
    bo_mesh = cx.bpy.data.objects.new('tmp', bm_data)
    bo_mesh.parent = parent
    cx.bpy.context.scene.objects.link(bo_mesh)
    bm = bmesh.new()
    bmfaces = []
    sgfuncs = (-1, lambda ga, gb, ea, eb: ga == gb) if cx.soc_sgroups else (-1, _cop_sgfunc)
    for (cid, data) in cr:
        if cid == Chunks.Mesh.VERTS:
            pr = PackedReader(data)
            for _ in range(pr.getf('I')[0]):
                bm.verts.new(read_v3f(pr))
        elif cid == Chunks.Mesh.FACES:
            fix_ensure_lookup_table(bm.verts)
            pr = PackedReader(data)
            for _ in range(pr.getf('I')[0]):
                fr = pr.getf('IIIIII')
                try:
                    bmfaces.append(bm.faces.new((bm.verts[fr[0]], bm.verts[fr[4]], bm.verts[fr[2]])))
                except ValueError:
                    bmfaces.append(None)
            bm.normal_update()
        elif cid == Chunks.Mesh.MESHNAME:
            bo_mesh.name = PackedReader(data).gets()
            bm_data.name = bo_mesh.name + '.mesh'
        elif cid == Chunks.Mesh.SG:
            pr = PackedReader(data)
            bm_data.use_auto_smooth = True
            bm_data.auto_smooth_angle = math.pi
            edict = {}
            for fi, sg in enumerate(pr.getf(str(len(data) // 4) + 'I')):
                bmf = bmfaces[fi]
                if bmf is None:
                    debug('skip face: ' + str(fi))
                    continue
                if sg == sgfuncs[0]:
                    bmf.smooth = False
                    continue
                bmf.smooth = True
                for ei, bme in enumerate(bmf.edges):
                    x = edict.get(bme)
                    if x is None:
                        edict[bme] = (sg, ei)
                    elif not sgfuncs[1](x[0], sg, x[1], ei):
                        bme.smooth = False
        elif cid == Chunks.Mesh.SFACE:
            pr = PackedReader(data)
            for _ in range(pr.getf('H')[0]):
                n = pr.gets()
                um = cx.used_materials.get(n)
                if um is None:
                    cx.used_materials[n] = um = (cx.bpy.data.materials.new(n), [])
                bmat, meshes = um
                meshes.append(bm_data)
                midx = len(bm_data.materials)
                bm_data.materials.append(bmat)
                for fi in pr.getf(str(pr.getf('I')[0]) + 'I'):
                    bmf = bmfaces[fi]
                    if bmf is None:
                        debug('skip face: ' + str(fi))
                        continue
                    bmf.material_index = midx
        elif cid == Chunks.Mesh.VMREFS:
            pass  # we use data from vmaps
        elif cid == Chunks.Mesh.VMAPS2:
            pr = PackedReader(data)
            for _ in range(pr.getf('I')[0]):
                n = pr.gets()
                dim = pr.getf('B')[0]    # dim
                discon = pr.getf('B')[0] != 0
                typ = pr.getf('B')[0] & 0x3
                sz = pr.getf('I')[0]
                if typ == 0:
                    bml = bm.loops.layers.uv.get(n)
                    if bml is None:
                        bml = bm.loops.layers.uv.new(n)
                    uvs = [pr.getf('ff') for __ in range(sz)]
                    vtx = pr.getf(str(sz) + 'I')
                    if discon:
                        fcs = pr.getf(str(sz) + 'I')
                        for uv, vi, fi in zip(uvs, vtx, fcs):
                            bmf = bmfaces[fi]
                            if bmf is None:
                                debug('skip face: ' + str(fi))
                                continue
                            for l, v in zip(bmf.loops, bmf.verts):
                                if v.index == vi:
                                    l[bml].uv = (uv[0], 1 - uv[1])
                                    break
                    else:
                        for uv, vi in zip(uvs, vtx):
                            for l in bm.verts[vi].link_loops:
                                l[bml].uv = (uv[0], 1 - uv[1])
                elif typ == 1:  # weights
                    bml = bm.verts.layers.deform.verify()
                    vgi = len(bo_mesh.vertex_groups)
                    bo_mesh.vertex_groups.new(name=n)
                    wgs = pr.getf(str(sz) + 'f')
                    vtx = pr.getf(str(sz) + 'I')
                    if discon:
                        fcs = pr.getf(str(sz) + 'I')
                    else:
                        for vw, vi in zip(wgs, vtx):
                            bm.verts[vi][bml][vgi] = vw
                else:
                    raise Exception('unknown vmap type: ' + str(typ))
        elif cid == Chunks.Mesh.FLAGS:
            bo_mesh.data.xray.flags = PackedReader(data).getf('B')[0]
            if bo_mesh.data.xray.flags & 0x4:  # sgmask
                sgfuncs = (0, lambda ga, gb, ea, eb: bool(ga & gb))
        elif cid == Chunks.Mesh.BBOX:
            pass  # blender automatically calculates bbox
        elif cid == Chunks.Mesh.OPTIONS:
            bo_mesh.data.xray.options = PackedReader(data).getf('II')
        else:
            warn_imknown_chunk(cid, 'mesh')
    bm.to_mesh(bm_data)
    return bo_mesh


def _get_fake_bone_shape():
    r = bpy.data.objects.get('fake_bone_shape')
    if r is None:
        r = bpy.data.objects.new('fake_bone_shape', None)
        r.empty_draw_size = 0
    return r


def _get_real_bone_shape():
    r = bpy.data.objects.get('real_bone_shape')
    if r is None:
        r = bpy.data.objects.new('real_bone_shape', None)
        r.empty_draw_type = 'SPHERE'
        r.empty_draw_size = 0.3
    return r


__matrix_bone = mathutils.Matrix(((1.0, 0.0, 0.0, 0.0), (0.0, 0.0, -1.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
__matrix_bone_inv = __matrix_bone.inverted()


def _import_bone(cx, cr, bpy_arm_obj, renamemap):
    bpy_armature = bpy_arm_obj.data
    ver = cr.nextf(Chunks.Bone.VERSION, 'H')[0]
    if ver != 0x2:
        raise Exception('unsupported BONE format version: {}'.format(ver))
    pr = PackedReader(cr.next(Chunks.Bone.DEF))
    name = pr.gets()
    parent = pr.gets()
    vmap = pr.gets()
    if name != vmap:
        ex = renamemap.get(vmap, None)
        if ex is None:
            cx.report({'WARNING'}, 'Bone VMap: {} will be renamed to {}'.format(vmap, name))
        elif ex != name:
            cx.report({'WARNING'}, 'Bone VMap multiple renaming: {} will be renamed to {} and then to {}'.format(vmap, ex, name))
        renamemap[vmap] = name
    pr = PackedReader(cr.next(Chunks.Bone.BIND_POSE))
    offset = read_v3f(pr)
    rotate = read_v3f(pr)
    length = pr.getf('f')[0]
    cx.bpy.ops.object.mode_set(mode='EDIT')
    try:
        bpy_bone = bpy_armature.edit_bones.new(name=name)
        mr = mathutils.Euler((-rotate[0], -rotate[1], -rotate[2]), 'YXZ').to_matrix().to_4x4()
        mat = mathutils.Matrix.Translation(offset) * mr * __matrix_bone
        if parent:
            bpy_bone.parent = bpy_armature.edit_bones[parent]
            mat = bpy_bone.parent.matrix * __matrix_bone_inv * mat
        bpy_bone.tail.y = 0.05
        bpy_bone.matrix = mat
        name = bpy_bone.name
    finally:
        cx.bpy.ops.object.mode_set(mode='OBJECT')
    bp = bpy_arm_obj.pose.bones[name]
    if cx.op.shaped_bones:
        bp.custom_shape = _get_real_bone_shape()
    xray = bpy_armature.bones[name].xray
    xray.version = cx.version
    xray.length = length
    for (cid, data) in cr:
        if cid == Chunks.Bone.DEF:
            s = PackedReader(data).gets()
            if name != s:
                cx.report({'WARNING'}, 'Not supported yet! bone name({}) != bone def2({})'.format(name, s))
        elif cid == Chunks.Bone.MATERIAL:
            xray.gamemtl = PackedReader(data).gets()
        elif cid == Chunks.Bone.SHAPE:
            pr = PackedReader(data)
            xray.shape.type = str(pr.getf('H')[0])
            xray.shape.flags = pr.getf('H')[0]
            xray.shape.box_rot = pr.getf('fffffffff')
            xray.shape.box_trn = pr.getf('fff')
            xray.shape.box_hsz = pr.getf('fff')
            xray.shape.sph_pos = pr.getf('fff')
            xray.shape.sph_rad = pr.getf('f')[0]
            xray.shape.cyl_pos = pr.getf('fff')
            xray.shape.cyl_dir = pr.getf('fff')
            xray.shape.cyl_hgh = pr.getf('f')[0]
            xray.shape.cyl_rad = pr.getf('f')[0]
        elif cid == Chunks.Bone.IK_JOINT:
            pr = PackedReader(data)
            xray.ikjoint.type = str(pr.getf('I')[0])
            bp.use_ik_limit_x = True
            bp.ik_min_x, bp.ik_max_x = pr.getf('ff')
            xray.ikjoint.lim_x_spr, xray.ikjoint.lim_x_dmp = pr.getf('ff')
            bp.use_ik_limit_y = True
            bp.ik_min_y, bp.ik_max_y = pr.getf('ff')
            xray.ikjoint.lim_y_spr, xray.ikjoint.lim_y_dmp = pr.getf('ff')
            bp.use_ik_limit_z = True
            bp.ik_min_z, bp.ik_max_z = pr.getf('ff')
            xray.ikjoint.lim_z_spr, xray.ikjoint.lim_z_dmp = pr.getf('ff')
            xray.ikjoint.spring = pr.getf('f')[0]
            xray.ikjoint.damping = pr.getf('f')[0]
        elif cid == Chunks.Bone.MASS_PARAMS:
            pr = PackedReader(data)
            xray.mass.value = pr.getf('f')[0]
            xray.mass.center = read_v3f(pr)
        elif cid == Chunks.Bone.IK_FLAGS:
            xray.ikflags = PackedReader(data).getf('I')[0]
        elif cid == Chunks.Bone.BREAK_PARAMS:
            pr = PackedReader(data)
            xray.breakf.force = pr.getf('f')[0]
            xray.breakf.torque = pr.getf('f')[0]
        elif cid == Chunks.Bone.FRICTION:
            xray.friction = PackedReader(data).getf('f')[0]
        else:
            warn_imknown_chunk(cid, 'bone')


def _import_main(fpath, cx, cr):
    object_name = os.path.basename(fpath.lower())
    ver = cr.nextf(Chunks.Object.VERSION, 'H')[0]
    if ver != 0x10:
        raise Exception('unsupported OBJECT format version: {:#x}'.format(ver))
    if cx.bpy:
        bpy_obj = cx.bpy.data.objects.new(object_name, None)
        bpy_obj.xray.version = cx.version
        cx.bpy.context.scene.objects.link(bpy_obj)
    else:
        bpy_obj = None

    bpy_armature = None
    bones_renamemap = {}
    meshes = []
    for (cid, data) in cr:
        if cid == Chunks.Object.MESHES:
            for (_, mdat) in ChunkedReader(data):
                meshes.append(_import_mesh(cx, ChunkedReader(mdat), bpy_obj))
        elif (cid == Chunks.Object.SURFACES1) or (cid == Chunks.Object.SURFACES2):
            uvmaps = {}
            for mesh in meshes:
                for uvl in mesh.data.uv_layers:
                    key = uvl.name.lower()
                    layers = uvmaps.get(key, None)
                    if layers is None:
                        uvmaps[key] = layers = []
                    layers.append(uvl)

            pr = PackedReader(data)
            for _ in range(pr.getf('I')[0]):
                n = pr.gets()
                eshader = pr.gets()
                cshader = pr.gets()
                gamemtl = pr.gets() if cid == Chunks.Object.SURFACES2 else 'default'
                texture = pr.gets()
                vmap = pr.gets()
                for l in uvmaps.get(vmap.lower(), []):
                    if l.name != vmap:
                        cx.report({'WARNING'}, 'Texture VMap: {} renamed to {}'.format(l.name, vmap))
                        l.name = vmap
                flags = pr.getf('I')[0]
                pr.getf('I')    # fvf
                pr.getf('I')    # ?
                um = cx.used_materials.get(n)
                if um is None:
                    cx.report({'WARNING'}, 'No material found for surface: ' + n)
                    continue
                del cx.used_materials[n]
                bpy_material = None
                for bm in bpy.data.materials:
                    if not bm.name.startswith(n):
                        continue
                    if bm.xray.flags != flags:
                        continue
                    if bm.xray.eshader != eshader:
                        continue
                    if bm.xray.cshader != cshader:
                        continue
                    if bm.xray.gamemtl != gamemtl:
                        continue
                    ts_found = False
                    tx_filepart = texture.replace('\\', os.path.sep)
                    for ts in bm.texture_slots:
                        if not ts:
                            continue
                        if ts.uv_layer != vmap:
                            continue
                        if not hasattr(ts.texture, 'image'):
                            continue
                        if not tx_filepart in ts.texture.image.filepath:
                            continue
                        ts_found = True
                        break
                    if not ts_found:
                        continue
                    bpy_material = bm
                    break
                if bpy_material:
                    bmap, um_meshes = um
                    for d in um_meshes:
                        for i, m in enumerate(d.materials):
                            if m == bmap:
                                d.materials[i] = bpy_material
                    bpy.data.materials.remove(bmap)
                else:
                    bpy_material = um[0]
                    bpy_material.xray.flags = flags
                    bpy_material.xray.eshader = eshader
                    bpy_material.xray.cshader = cshader
                    bpy_material.xray.gamemtl = gamemtl
                    if texture:
                        bpy_texture = cx.bpy.data.textures.get(texture)
                        if bpy_texture is None:
                            bpy_texture = cx.bpy.data.textures.new(texture, type='IMAGE')
                            bpy_texture.image = cx.image(texture)
                        bpy_texture_slot = bpy_material.texture_slots.add()
                        bpy_texture_slot.texture = bpy_texture
                        bpy_texture_slot.texture_coords = 'UV'
                        bpy_texture_slot.uv_layer = vmap
                        bpy_texture_slot.use_map_color_diffuse = True
        elif cid == Chunks.Object.BONES1:
            if cx.bpy and (bpy_armature is None):
                bpy_armature = cx.bpy.data.armatures.new(object_name)
                bpy_armature.use_auto_ik = True
                bpy_armature.xray.version = cx.version
                bpy_arm_obj = cx.bpy.data.objects.new(object_name, bpy_armature)
                bpy_arm_obj.show_x_ray = True
                bpy_arm_obj.parent = bpy_obj
                cx.bpy.context.scene.objects.link(bpy_arm_obj)
                cx.bpy.context.scene.objects.active = bpy_arm_obj
            for (_, bdat) in ChunkedReader(data):
                _import_bone(cx, ChunkedReader(bdat), bpy_arm_obj, bones_renamemap)
            cx.bpy.ops.object.mode_set(mode='EDIT')
            try:
                import mathutils
                bone_childrens = {}
                for b in bpy_armature.edit_bones:
                    p = b.parent
                    if not p:
                        continue
                    bc = bone_childrens.get(p.name)
                    if bc is None:
                        bone_childrens[p.name] = bc = []
                    bc.append(b)
                fake_names = []
                for b in bpy_armature.edit_bones:
                    bc = bone_childrens.get(b.name)
                    if bc:
                        if cx.op.shaped_bones:
                            avg = mathutils.Vector()
                            for c in bc:
                                avg += c.head
                            b.length = max(b.length, (avg / len(bc) - b.head).dot(b.vector.normalized()))
                        for c in bc:
                            if bpy_armature.bones[c.name].xray.ikjoint.type == '0':  # rigid
                                continue
                            fb = bpy_armature.edit_bones.new(name=c.name+'.fake')
                            fb.use_deform = False
                            fb.hide = True
                            fb.parent = b
                            fb.use_connect = True
                            fb.tail = c.head
                            c.parent = fb
                            c.use_connect = True
                            fake_names.append(fb.name)
            finally:
                cx.bpy.ops.object.mode_set(mode='OBJECT')
            for b in bpy_arm_obj.pose.bones:
                b.rotation_mode = 'ZXY'
            for n in fake_names:
                b = bpy_arm_obj.pose.bones.get(n)
                if b:
                    b.lock_ik_x = b.lock_ik_y = b.lock_ik_z = True
                    b.custom_shape = _get_fake_bone_shape()
                b = bpy_armature.bones.get(n)
                if b:
                    b.hide = True
            for o in meshes:
                bpy_armmod = o.modifiers.new(name='Armature', type='ARMATURE')
                bpy_armmod.object = bpy_arm_obj
        elif cid == Chunks.Object.TRANSFORM:
            pr = PackedReader(data)
            pos = read_v3f(pr)
            rot = read_v3f(pr)
            import mathutils
            bpy_obj.matrix_basis *= mathutils.Matrix.Translation(pos) * mathutils.Euler(rot, 'YXZ').to_matrix().to_4x4()
        elif cid == Chunks.Object.FLAGS:
            bpy_obj.xray.flags = PackedReader(data).getf('I')[0]
        elif cid == Chunks.Object.USERDATA:
            bpy_obj.xray.userdata = PackedReader(data).gets(onerror=lambda e: cx.report({'WARNING'}, 'Object: bad userdata: {}'.format(e)))
        elif cid == Chunks.Object.LOD_REF:
            bpy_obj.xray.lodref = PackedReader(data).gets()
        elif cid == Chunks.Object.REVISION:
            pr = PackedReader(data)
            bpy_obj.xray.revision.owner = pr.gets()
            bpy_obj.xray.revision.ctime = pr.getf('I')[0]
            bpy_obj.xray.revision.moder = pr.gets()
            bpy_obj.xray.revision.mtime = pr.getf('I')[0]
        elif cid == Chunks.Object.PARTITIONS1:
            cx.bpy.context.scene.objects.active = bpy_arm_obj
            cx.bpy.ops.object.mode_set(mode='POSE')
            try:
                pr = PackedReader(data)
                for _ in range(pr.getf('I')[0]):
                    cx.bpy.ops.pose.group_add()
                    bg = bpy_arm_obj.pose.bone_groups.active
                    bg.name = pr.gets()
                    for __ in range(pr.getf('I')[0]):
                        bn = pr.gets()
                        bpy_arm_obj.pose.bones[bn].bone_group = bg
            finally:
                cx.bpy.ops.object.mode_set(mode='OBJECT')
        elif cid == Chunks.Object.MOTION_REFS:
            bpy_obj.xray.motionrefs = PackedReader(data).gets()
        elif cid == Chunks.Object.MOTIONS:
            if not cx.import_motions:
                continue

            def fcurve_set(curve, time, value):
                if curve.evaluate(time) != value:
                    curve.keyframe_points.insert(time, value)

            pr = PackedReader(data)
            for _ in range(pr.getf('I')[0]):
                a = bpy.data.actions.new(name=pr.gets())
                a.use_fake_user = True
                xr = a.xray
                pr.getf('II')  # range
                fps = pr.getf('f')[0]
                ver = pr.getf('H')[0]
                xr.fps = fps
                if ver == 6:
                    xr.flags, xr.bonepart = pr.getf('<BH')
                    xr.speed, xr.accrue, xr.falloff, xr.power = pr.getf('<ffff')
                    for _1 in range(pr.getf('H')[0]):
                        tmpfc = [a.fcurves.new('temp', i) for i in range(6)]
                        times = {}
                        bname = pr.gets()
                        flags = pr.getf('B')[0]
                        if flags != 0:
                            cx.report({'WARNING'}, 'bone "{}" flags == {}'.format(bname, flags))
                        for i in range(6):
                            behaviours = pr.getf('BB')
                            if (behaviours[0] != 1) or (behaviours[1] != 1):
                                cx.report({'WARNING'}, 'bone "{}" behaviours == {}'.format(bname, behaviours))
                            fc = tmpfc[i]
                            for _3 in range(pr.getf('H')[0]):
                                v = pr.getf('f')[0]
                                t = pr.getf('f')[0] * fps
                                times[t] = True
                                fc.keyframe_points.insert(t, v)
                                shape = Shape(pr.getf('B')[0])
                                if shape != Shape.STEPPED:
                                    pr.getf('HHH')
                                    pr.getf('HHHH')
                        dp = 'pose.bones["' + bname + '"]'
                        fcs = [
                            a.fcurves.new(dp + '.location', 0, bname),
                            a.fcurves.new(dp + '.location', 1, bname),
                            a.fcurves.new(dp + '.location', 2, bname),
                            a.fcurves.new(dp + '.rotation_euler', 0, bname),
                            a.fcurves.new(dp + '.rotation_euler', 1, bname),
                            a.fcurves.new(dp + '.rotation_euler', 2, bname)
                        ]
                        bpy_bone = bpy_armature.bones[bname]
                        xm = bpy_bone.matrix_local.inverted()
                        real_parent = find_bone_real_parent(bpy_bone)
                        if real_parent:
                            xm = xm * real_parent.matrix_local
                        else:
                            xm = xm * __matrix_bone
                        for t in times.keys():
                            tr = (tmpfc[0].evaluate(t), tmpfc[1].evaluate(t), -tmpfc[2].evaluate(t))
                            rt = (-tmpfc[4].evaluate(t), -tmpfc[3].evaluate(t), tmpfc[5].evaluate(t))
                            mat = xm * mathutils.Matrix.Translation(tr) * mathutils.Euler(rt, 'ZXY').to_matrix().to_4x4()
                            tr = mat.to_translation()
                            rt = mat.to_euler('ZXY')
                            for _4 in range(3):
                                fcurve_set(fcs[_4 + 0], t, tr[_4])
                            for _4 in range(3):
                                fcurve_set(fcs[_4 + 3], t, rt[_4])
                        for fc in tmpfc:
                            a.fcurves.remove(fc)
                else:
                    raise Exception('unsupported motions version: {}'.format(ver))
        else:
            warn_imknown_chunk(cid, 'main')
    for m in meshes:
        for vg in m.vertex_groups:
            nn = bones_renamemap.get(vg.name, None)
            if nn is not None:
                vg.name = nn
        for p, u in zip(m.data.polygons, m.data.uv_textures[0].data):
            bmat = m.data.materials[p.material_index]
            u.image = bmat.active_texture.image


def _import(fpath, cx, cr):
    for (cid, data) in cr:
        if cid == Chunks.Object.MAIN:
            _import_main(fpath, cx, ChunkedReader(data))
        else:
            warn_imknown_chunk(cid, 'root')


def import_file(fpath, cx):
    with io.open(fpath, 'rb') as f:
        _import(fpath, cx, ChunkedReader(f.read()))
