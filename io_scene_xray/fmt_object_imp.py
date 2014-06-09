import io
import math
import os.path
from .xray_io import ChunkedReader, PackedReader
from .fmt_object import Chunks


class ImportContext:
    def __init__(self, fpath, gamedata, report, bpy=None):
        self.file_path = fpath
        self.object_name = os.path.basename(fpath.lower())
        self.report = report
        self.bpy = bpy
        self.gamedata_folder = gamedata
        self.__images = {}

    def image(self, relpath):
        relpath = relpath.lower().replace('\\', os.path.sep)
        result = self.__images.get(relpath)
        if result is None:
            self.__images[relpath] = result = self.bpy.data.images.load('{}/textures/{}.dds'.format(self.gamedata_folder, relpath))
        return result


def warn_imknown_chunk(cid, location):
    print('WARNING: UNKNOWN CHUNK: {:#x} IN: {}'.format(cid, location))


def _remap(v, unimap, array):
    r = unimap.get(v)
    if r is None:
        unimap[v] = r = len(array)
        array.append(v)
    return r


class VMap:
    def __init__(self, name, dimensions, discontinous):
        self.name = name
        self.dimensions = dimensions
        self.data = []
        self.vertices = []
        if discontinous:
            self.faces = []
        else:
            self.faces = None

    def init(self, bpy_obj):
        pass


class UVMap(VMap):
    def init(self, bpy_obj):
        bpy_mesh = bpy_obj.data
        uv_l = bpy_mesh.uv_layers.get(self.name)
        if uv_l is None:
            uv_t = bpy_mesh.uv_textures.new(name=self.name)
            uv_l = bpy_mesh.uv_layers.get(uv_t.name)

        def func(i, vi, d):
            uv_l.data[i].uv = (d[0], 1 - d[1])

        return func


class WMap(VMap):
    def init(self, bpy_obj):
        vg = bpy_obj.vertex_groups.get(self.name)
        if vg is None:
            vg = bpy_obj.vertex_groups.new(name=self.name)

        def func(i, vi, d):
            vg.add([vi], d, 'REPLACE')

        return func


def _import_mesh(cx, cr, parent):
    ver = cr.nextf(Chunks.Mesh.VERSION, 'H')[0]
    if ver != 0x11:
        raise Exception('unsupported MESH format version: {:#x}'.format(ver))
    vertices = []
    faces = []
    meshname = ''
    smoothing_groups = []
    surfaces = {}
    vmrefs = []
    vmaps = []
    flags = 0
    for (cid, data) in cr:
        if cid == Chunks.Mesh.VERTS:
            pr = PackedReader(data)
            vc = pr.getf('I')[0]
            vertices = [pr.getf('fff') for _ in range(vc)]
        elif cid == Chunks.Mesh.FACES:
            pr = PackedReader(data)
            fc = pr.getf('I')[0]
            for _ in range(fc):
                fr = pr.getf('IIIIII')
                faces.append(((fr[0], fr[2], fr[4]), (fr[1], fr[3], fr[5])))
        elif cid == Chunks.Mesh.MESHNAME:
            meshname = PackedReader(data).gets()
        elif cid == Chunks.Mesh.SG:
            pr = PackedReader(data)
            smoothing_groups = [pr.getf('I')[0] for _ in range(len(data) // 4)]
        elif cid == Chunks.Mesh.SFACE:
            pr = PackedReader(data)
            for _ in range(pr.getf('H')[0]):
                n = pr.gets()
                surfaces[n] = [pr.getf('I')[0] for __ in range(pr.getf('I')[0])]
        elif cid == Chunks.Mesh.VMREFS:
            pr = PackedReader(data)
            for _ in range(pr.getf('I')[0]):
                vmrefs.append([pr.getf('II') for __ in range(pr.getf('B')[0])])
        elif cid == Chunks.Mesh.VMAPS2:
            pr = PackedReader(data)
            for _ in range(pr.getf('I')[0]):
                n = pr.gets()
                dim = pr.getf('B')[0]    # dim
                discon = pr.getf('B')[0] != 0
                typ = pr.getf('B')[0] & 0x3
                sz = pr.getf('I')[0]
                if typ == 0:
                    vm = UVMap(n, dim, discon)
                    vm.data = [pr.getf('ff') for __ in range(sz)]
                elif typ == 1:  # weights
                    vm = WMap(n, dim, discon)
                    vm.data = [pr.getf('f')[0] for __ in range(sz)]
                else:
                    raise Exception('unknown vmap type: ' + str(typ))
                vm.vertices = [pr.getf('I')[0] for __ in range(sz)]
                if discon:
                    vm.faces = [pr.getf('I')[0] for __ in range(sz)]
                vmaps.append(vm)
        elif cid == Chunks.Mesh.FLAGS:
            flags = PackedReader(data).getf('B')[0]
        else:
            warn_imknown_chunk(cid, 'mesh')

    by_surface = {}
    if cx.bpy:
        bo_mesh = cx.bpy.data.objects.new(meshname, None)
        bo_mesh.parent = parent
        cx.bpy.context.scene.objects.link(bo_mesh)
        bo_mesh.xray.flags = flags

        for (sn, sf) in surfaces.items():
            bm_sf = cx.bpy.data.meshes.new(sn + '.mesh')
            vtx = []
            fcs = []
            rfs = []
            smgroups = {}
            for fi in sf:
                f = faces[fi][0]
                sgi = smoothing_groups[fi]
                sg = smgroups.get(sgi)
                if sg is None:
                    smgroups[sgi] = sg = {}
                fcs.append((
                    _remap(f[0], sg, vtx),
                    _remap(f[1], sg, vtx),
                    _remap(f[2], sg, vtx)
                ))
                rfs.append(faces[fi][1])
            bm_sf.from_pydata([vertices[i] for i in vtx], [], fcs)

            bo_sf = cx.bpy.data.objects.new(sn, bm_sf)
            bo_sf.parent = bo_mesh
            cx.bpy.context.scene.objects.link(bo_sf)

            mmaps = {}
            for i in range(len(fcs)):
                f = fcs[i]
                ri = rfs[i]
                for vi in range(3):
                    for (vmi, vmo) in vmrefs[ri[vi]]:
                        m = mmaps.get(vmi)
                        vm = vmaps[vmi]
                        if m is None:
                            mmaps[vmi] = m = vm.init(bo_sf)
                        m(i * 3 + vi, f[vi], vm.data[vmo])
            bysf = by_surface.get(sn)
            if bysf is None:
                by_surface[sn] = bysf = []
            bysf.append(bo_sf)

            bmat = cx.bpy.data.materials.get(sn)
            if bmat is None:
                bmat = cx.bpy.data.materials.new(sn)
            bm_sf.materials.append(bmat)
    else:
        print('vertices: ' + str(vertices))
        print('faces: ' + str(faces))

    return by_surface


def _import_bone(cx, cr, bpy_armature, bonemat):
    ver = cr.nextf(Chunks.Bone.VERSION, 'H')[0]
    if ver != 0x2:
        raise Exception('unsupported BONE format version: {}'.format(ver))
    pr = PackedReader(cr.next(Chunks.Bone.DEF))
    name = pr.gets()
    parent = pr.gets()
    vmap = pr.gets()
    if name != vmap:
        cx.report({'WARNING'}, 'Not supported yet! bone name({}) != bone vmap({})'.format(name, vmap))
    pr = PackedReader(cr.next(Chunks.Bone.BIND_POSE))
    offset = pr.getf('fff')
    rotate = pr.getf('fff')
    length = pr.getf('f')[0]
    cx.bpy.ops.object.mode_set(mode='EDIT')
    try:
        bpy_bone = bpy_armature.edit_bones.new(name=name)
        if parent:
            bpy_bone.parent = bpy_armature.edit_bones[parent]
        import mathutils
        mat = bonemat.get(parent, mathutils.Matrix.Identity(4)) * mathutils.Matrix.Translation(offset) * mathutils.Euler(rotate, 'ZXY').to_matrix().to_4x4()
        bonemat[name] = mat
        bpy_bone.head = mat * mathutils.Vector()
        bpy_bone.tail = bpy_bone.head + mathutils.Vector([0, 0.1, 0])
    finally:
        cx.bpy.ops.object.mode_set(mode='OBJECT')
    xray = bpy_armature.bones[name].xray
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
            xray.shape.type = pr.getf('H')[0]
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
            xray.ikjoint.type = pr.getf('I')[0]
            xray.ikjoint.limits = pr.getf('fff')
            xray.ikjoint.lim_spr = pr.getf('f')[0]
            xray.ikjoint.lim_dmp = pr.getf('f')[0]
            xray.ikjoint.spring = pr.getf('f')[0]
            xray.ikjoint.damping = pr.getf('f')[0]
        elif cid == Chunks.Bone.MASS_PARAMS:
            pr = PackedReader(data)
            xray.mass.value = pr.getf('f')[0]
            xray.mass.center = pr.getf('fff')
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


def _import_main(cx, cr):
    ver = cr.nextf(Chunks.Object.VERSION, 'H')[0]
    if ver != 0x10:
        raise Exception('unsupported OBJECT format version: {:#x}'.format(ver))
    if cx.bpy:
        bpy_obj = cx.bpy.data.objects.new(cx.object_name, None)
        bpy_obj.rotation_euler.x = math.pi / 2
        bpy_obj.scale.z = -1
        cx.bpy.context.scene.objects.link(bpy_obj)
    else:
        bpy_obj = None

    bpy_armature = None
    by_surface = {}
    for (cid, data) in cr:
        if cid == Chunks.Object.MESHES:
            for (_, mdat) in ChunkedReader(data):
                for (k, v) in _import_mesh(cx, ChunkedReader(mdat), bpy_obj).items():
                    bs = by_surface.get(k)
                    if bs is None:
                        by_surface[k] = v
                    else:
                        bs += v
        elif cid == Chunks.Object.SURFACES2:
            pr = PackedReader(data)
            for _ in range(pr.getf('I')[0]):
                n = pr.gets()
                eshader = pr.gets()
                cshader = pr.gets()
                gamemtl = pr.gets()
                texture = pr.gets()
                vmap = pr.gets()
                flags = pr.getf('I')[0]
                pr.getf('I')    # fvf
                pr.getf('I')    # ?
                if cx.bpy:
                    bpy_material = cx.bpy.data.materials.get(n)
                    if bpy_material is None:
                        continue
                    bpy_material.xray.flags = flags
                    bpy_material.xray.eshader = eshader
                    bpy_material.xray.cshader = cshader
                    bpy_material.xray.gamemtl = gamemtl
                    if texture:
                        bpy_texture = cx.bpy.data.textures.get(texture)
                        if bpy_texture is None:
                            bpy_texture = cx.bpy.data.textures.new(texture, type='IMAGE')
                            bpy_texture.image = cx.image(texture)
                        img = bpy_texture.image
                        for o in by_surface.get(n):
                            for t in o.data.uv_textures:
                                for f in t.data.values():
                                    f.image = img
                        bpy_texture_slot = bpy_material.texture_slots.add()
                        bpy_texture_slot.texture = bpy_texture
                        bpy_texture_slot.texture_coords = 'UV'
                        bpy_texture_slot.uv_layer = vmap
                        bpy_texture_slot.use_map_color_diffuse = True
        elif cid == Chunks.Object.BONES1:
            if cx.bpy and (bpy_armature is None):
                bpy_armature = cx.bpy.data.armatures.new(cx.object_name)
                bpy_arm_obj = cx.bpy.data.objects.new(cx.object_name, bpy_armature)
                bpy_arm_obj.parent = bpy_obj
                cx.bpy.context.scene.objects.link(bpy_arm_obj)
                cx.bpy.context.scene.objects.active = bpy_arm_obj
            bonemat = {}
            for (_, bdat) in ChunkedReader(data):
                _import_bone(cx, ChunkedReader(bdat), bpy_armature, bonemat)
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
                for b in bpy_armature.edit_bones:
                    bc = bone_childrens.get(b.name)
                    if not bc:
                        p = b.parent
                        if p:
                            b.tail = b.head + (b.head - p.head).normalized() * 0.01
                        else:
                            b.tail = b.head + mathutils.Vector([0, 0.01, 0])
                    else:
                        avg = mathutils.Vector()
                        for c in bc:
                            avg += c.head
                        b.tail = avg / len(bc)
            finally:
                cx.bpy.ops.object.mode_set(mode='OBJECT')
            for oo in by_surface.values():
                for o in oo:
                    bpy_armmod = o.modifiers.new(name='Armature', type='ARMATURE')
                    bpy_armmod.object = bpy_arm_obj
        elif cid == Chunks.Object.TRANSFORM:
            pr = PackedReader(data)
            pos = pr.getf('fff')
            rot = pr.getf('fff')
            import mathutils
            bpy_obj.matrix_basis *= mathutils.Matrix.Translation(pos) * mathutils.Euler((-rot[0], -rot[1], -rot[2])).to_matrix().to_4x4()
        elif cid == Chunks.Object.FLAGS:
            bpy_obj.xray.flags = PackedReader(data).getf('I')[0]
        elif cid == Chunks.Object.USERDATA:
            bpy_obj.xray.userdata = PackedReader(data).gets()
        elif cid == Chunks.Object.LOD_REF:
            bpy_obj.xray.lodref = PackedReader(data).gets()
        elif cid == Chunks.Object.REVISION:
            pr = PackedReader(data)
            bpy_obj.xray.revision.owner = pr.gets()
            bpy_obj.xray.revision.ctime = pr.getf('I')[0]
            bpy_obj.xray.revision.moder = pr.gets()
            bpy_obj.xray.revision.mtime = pr.getf('I')[0]
        elif cid == Chunks.Object.MOTION_REFS:
            bpy_obj.xray.motionrefs = PackedReader(data).gets()
        else:
            warn_imknown_chunk(cid, 'main')


def _import(cx, cr):
    for (cid, data) in cr:
        if cid == Chunks.Object.MAIN:
            _import_main(cx, ChunkedReader(data))
        else:
            warn_imknown_chunk(cid, 'root')


def import_file(cx):
    with io.open(cx.file_path, 'rb') as f:
        _import(cx, ChunkedReader(f.read()))
