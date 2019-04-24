import math

import bpy
import bmesh

from ... import xray_io
from ... import utils
from ... import plugin_prefs
from ... import log
from .. import fmt
from . import main


_SHARP = 0xffffffff
_MIN_WEIGHT = 0.0002


def _cop_sgfunc(group_a, group_b, edge_a, edge_b):
    bfa, bfb = bool(group_a & 0x8), bool(group_b & 0x8)  # test backface-s
    if bfa != bfb:
        return False

    def is_soft(group, backface, edge):
        return (group & (4, 2, 1)[(4 - edge) % 3 if backface else edge]) == 0

    return is_soft(group_a, bfa, edge_a) and is_soft(group_b, bfb, edge_b)


@log.with_context(name='mesh')
def import_mesh(context, creader, renamemap):
    ver = creader.nextf(fmt.Chunks.Mesh.VERSION, 'H')[0]
    if ver != 0x11:
        raise utils.AppError(
            'unsupported MESH format version', log.props(version=ver)
        )
    mesh_name = None
    mesh_flags = None
    mesh_options = None
    bmsh = bmesh.new()
    sgfuncs = (_SHARP, lambda ga, gb, ea, eb: ga == gb) \
        if context.soc_sgroups else (_SHARP, _cop_sgfunc)
    vt_data = ()
    fc_data = ()

    face_sg = None
    s_faces = []
    vm_refs = ()
    vmaps = []
    vgroups = []
    bml_deform = bmsh.verts.layers.deform.verify()
    bml_texture = None
    has_sg_chunk = False
    for (cid, data) in creader:
        if cid == fmt.Chunks.Mesh.VERTS:
            reader = xray_io.PackedReader(data)
            vt_data = [main.read_v3f(reader) for _ in range(reader.int())]
        elif cid == fmt.Chunks.Mesh.FACES:
            s_6i = xray_io.PackedReader.prep('IIIIII')
            reader = xray_io.PackedReader(data)
            count = reader.int()
            fc_data = [reader.getp(s_6i) for _ in range(count)]
        elif cid == fmt.Chunks.Mesh.MESHNAME:
            mesh_name = xray_io.PackedReader(data).gets()
            log.update(name=mesh_name)
        elif cid == fmt.Chunks.Mesh.SG:
            if not data:    # old object format
                continue
            has_sg_chunk = True
            sgroups = data.cast('I')

            def face_sg_impl(bmf, fidx, edict):
                sm_group = sgroups[fidx]
                if sm_group == sgfuncs[0]:
                    bmf.smooth = False
                    for bme in bmf.edges:
                        bme.smooth = False
                    return
                bmf.smooth = True
                for eidx, bme in enumerate(bmf.edges):
                    prev = edict[bme.index]
                    if prev is None:
                        edict[bme.index] = (sm_group, eidx)
                    elif not sgfuncs[1](prev[0], sm_group, prev[1], eidx):
                        bme.smooth = False
            face_sg = face_sg_impl
        elif cid == fmt.Chunks.Mesh.SFACE:
            reader = xray_io.PackedReader(data)
            for _ in range(reader.getf('H')[0]):
                name = reader.gets()
                s_faces.append((name, reader.getb(reader.int() * 4).cast('I')))
        elif cid == fmt.Chunks.Mesh.VMREFS:
            s_ii = xray_io.PackedReader.prep('II')

            def read_vmref(reader):
                count = reader.byte()
                if count == 1:
                    return (reader.getp(s_ii),)  # fast path
                return [reader.getp(s_ii) for __ in range(count)]

            reader = xray_io.PackedReader(data)
            vm_refs = [read_vmref(reader) for _ in range(reader.int())]
        elif cid in (fmt.Chunks.Mesh.VMAPS1, fmt.Chunks.Mesh.VMAPS2):
            suppress_rename_warnings = {}
            reader = xray_io.PackedReader(data)
            for _ in range(reader.int()):
                name = reader.gets()
                if not name:
                    name = 'Texture'
                reader.skip(1)  # dim
                if cid == fmt.Chunks.Mesh.VMAPS2:
                    discon = reader.byte() != 0
                typ = reader.byte() & 0x3
                size = reader.int()
                if typ == 0:
                    new_name = renamemap.get(name.lower(), name)
                    if new_name != name:
                        if suppress_rename_warnings.get(name, None) != new_name:
                            log.warn(
                                'texture VMap has been renamed',
                                old=name,
                                new=new_name
                            )
                            suppress_rename_warnings[name] = new_name
                        name = new_name
                    bml = bmsh.loops.layers.uv.get(name)
                    if bml is None:
                        bml = bmsh.loops.layers.uv.new(name)
                        bml_texture = bmsh.faces.layers.tex.new(name)
                    uvs = reader.getb(size * 8).cast('f')
                    if cid == fmt.Chunks.Mesh.VMAPS2:
                        reader.skip(size * 4)
                        if discon:
                            reader.skip(size * 4)
                    vmaps.append((typ, bml, uvs))
                elif typ == 1:  # weights
                    name = renamemap.get(name, name)
                    vgi = len(vgroups)
                    vgroups.append(name)
                    wgs = reader.getb(size * 4).cast('f')
                    bad = False
                    for i, weight in enumerate(wgs):
                        if weight < _MIN_WEIGHT:
                            if not bad:
                                wgs = list(wgs)
                            bad = True
                            wgs[i] = _MIN_WEIGHT
                    if bad:
                        log.warn(
                            'weight VMap has values that are close to zero',
                            vmap=name
                        )
                    if cid == fmt.Chunks.Mesh.VMAPS2:
                        reader.skip(size * 4)
                        if discon:
                            reader.skip(size * 4)
                    vmaps.append((typ, vgi, wgs))
                else:
                    raise utils.AppError(
                        'unknown vmap type', log.props(type=typ)
                    )
        elif cid == fmt.Chunks.Mesh.FLAGS:
            mesh_flags = xray_io.PackedReader(data).getf('B')[0]
            if mesh_flags & 0x4:  # sgmask
                sgfuncs = (0, lambda ga, gb, ea, eb: bool(ga & gb))
        elif cid == fmt.Chunks.Mesh.BBOX:
            pass  # blender automatically calculates bbox
        elif cid == fmt.Chunks.Mesh.OPTIONS:
            mesh_options = xray_io.PackedReader(data).getf('II')
        elif cid == fmt.Chunks.Mesh.NOT_USED_0:
            pass  # not used chunk
        else:
            log.debug('unknown chunk', cid=cid)

    bo_mesh = None
    bad_vgroup = -1

    class LocalAbstract:
        def __init__(self, level=0, badvg=-1):
            self.__level = level
            self.__badvg = badvg
            self.__next = None

        def mkface(self, face_index):
            fr = fc_data[face_index]
            bmf = self._mkf(fr, 0, 4, 2)
            if bmf is None:
                return bmf
            for i, j in enumerate((1, 5, 3)):
                for vmi, vi in vm_refs[fr[j]]:
                    vmap = vmaps[vmi]
                    if vmap[0] == 0:
                        vi *= 2
                        vd = vmap[2]
                        bmf.loops[i][vmap[1]].uv = (vd[vi], 1 - vd[vi + 1])
            return bmf

        def _vtx(self, _fr, _i):
            raise 'abstract'

        def _vgvtx(self, vtx):
            if self.__badvg != -1:
                vtx[bml_deform][self.__badvg] = 0

        def _mkf(self, fr, i0, i1, i2):
            vertexes = (
                self._vtx(fr, i0), self._vtx(fr, i1), self._vtx(fr, i2)
            )
            try:
                return bmsh.faces.new(vertexes)
            except ValueError:
                if len(set(vertexes)) < 3:
                    log.warn('invalid face found')
                    return None
                if self.__next is None:
                    lvl = self.__level
                    if lvl > 100:
                        raise utils.AppError('too many duplicated polygons')
                    nonlocal bad_vgroup
                    if bad_vgroup == -1:
                        bad_vgroup = len(bo_mesh.vertex_groups)
                        bo_mesh.vertex_groups.new(utils.BAD_VTX_GROUP_NAME)
                    self.__next = self.__class__(lvl + 1, badvg=bad_vgroup)
                return self.__next._mkf(fr, i0, i1, i2)

    class LocalSimple(LocalAbstract):  # fastpath
        def __init__(self, level=0, badvg=-1):
            super(LocalSimple, self).__init__(level, badvg)
            self.__verts = [None] * len(vt_data)

        def _vtx(self, fr, i):
            vidx = fr[i]
            vertex = self.__verts[vidx]
            if vertex is None:
                self.__verts[vidx] = vertex = bmsh.verts.new(vt_data[vidx])
            self._vgvtx(vertex)
            return vertex

    class LocalComplex(LocalAbstract):
        def __init__(self, level=0, badvg=-1):
            super(LocalComplex, self).__init__(level, badvg)
            self.__verts = {}

        def _vtx(self, fr, i):
            vidx = fr[i]
            vkey = [vidx]
            for vmi, vei in vm_refs[fr[i + 1]]:
                vmap = vmaps[vmi]
                if vmap[0] == 1:
                    vkey.append((vmap[1], vmap[2][vei]))
            vkey = tuple(vkey)

            vertex = self.__verts.get(vkey, None)
            if vertex is None:
                self.__verts[vkey] = vertex = bmsh.verts.new(vt_data[vidx])
                for vl, vv in vkey[1:]:
                    vertex[bml_deform][vl] = vv
            self._vgvtx(vertex)
            return vertex

    bmfaces = [None] * len(fc_data)

    bm_data = bpy.data.meshes.new(mesh_name)
    if face_sg:
        bm_data.use_auto_smooth = True
        bm_data.auto_smooth_angle = math.pi
        bm_data.show_edge_sharp = True

    bo_mesh = bpy.data.objects.new(mesh_name, bm_data)
    if mesh_flags is not None:
        bo_mesh.data.xray.flags = mesh_flags
    if mesh_options is not None:
        bo_mesh.data.xray.options = mesh_options
    for vgroup in vgroups:
        bo_mesh.vertex_groups.new(vgroup)

    f_facez = []
    images = []
    for name, faces in s_faces:
        bmat = context.loaded_materials.get(name)
        if bmat is None:
            context.loaded_materials[name] = bmat = \
                bpy.data.materials.new(name)
            bmat.xray.version = context.version
        midx = len(bm_data.materials)
        bm_data.materials.append(bmat)
        images.append(
            bmat.active_texture.image if bmat.active_texture else None
        )
        f_facez.append((faces, midx))

    local_class = LocalComplex if vgroups else LocalSimple

    if context.split_by_materials:
        for faces, midx in f_facez:
            local = local_class()
            for fidx in faces:
                bmf = bmfaces[fidx]
                if bmf is not None:
                    log.warn(
                        'face has already been instantiated with material',
                        face=fidx,
                        material=bmf.material_index,
                    )
                    continue
                bmfaces[fidx] = bmf = local.mkface(fidx)
                if bmf is None:
                    continue
                bmf.material_index = midx
                if bml_texture is not None:
                    bmf[bml_texture].image = images[midx]

    local = local_class()
    for fidx, bmf in enumerate(bmfaces):
        if bmf is not None:
            continue  # already instantiated
        bmfaces[fidx] = local.mkface(fidx)

    if face_sg:
        bmsh.edges.index_update()
        edict = [None] * len(bmsh.edges)
        for fidx, bmf in enumerate(bmfaces):
            if bmf is None:
                continue
            face_sg(bmf, fidx, edict)

    if not context.split_by_materials:
        assigned = [False] * len(bmfaces)
        for faces, midx in f_facez:
            for fidx in faces:
                bmf = bmfaces[fidx]
                if bmf is None:
                    continue
                if assigned[fidx]:
                    log.warn(
                        'face has already already used material',
                        face=fidx,
                        material=bmf.material_index,
                    )
                    continue
                bmf.material_index = midx
                if bml_texture is not None:
                    bmf[bml_texture].image = images[midx]
                assigned[fidx] = True

    if bad_vgroup != -1:
        msg = 'duplicate faces found, "{}" vertex groups created'.format(
            bo_mesh.vertex_groups[bad_vgroup].name
        )
        if not context.split_by_materials:
            msg += ' (try to use "{}" option)'.format(
                plugin_prefs.PropObjectMeshSplitByMaterials()[1].get('name')
            )
        log.warn(msg)

    if not has_sg_chunk:    # old object format
        for face in bmsh.faces:
            face.smooth = True

    bmsh.normal_update()
    bmsh.to_mesh(bm_data)

    return bo_mesh
