# standart modules
import math

# blender modules
import bpy
import bmesh
import mathutils

# addon modules
from .. import fmt
from ... import ie
from .... import text
from .... import log
from .... import rw
from .... import utils


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
    ver = creader.nextf(fmt.Chunks.Mesh.VERSION, '<H')[0]
    if ver != fmt.CURRENT_MESH_VERSION:
        raise log.AppError(
            text.error.object_unsupport_mesh_ver,
            log.props(version=ver)
        )
    mesh_name = None
    mesh_flags = None
    mesh_options = None
    bmsh = bmesh.new()
    sgfuncs = (_SHARP, lambda ga, gb, ea, eb: ga == gb) \
        if context.soc_sgroups else (_SHARP, _cop_sgfunc)
    vt_data = ()
    fc_data = ()

    prefs = utils.version.get_preferences()

    face_sg = None
    s_faces = []
    split_normals = []
    vm_refs = ()
    vmaps = []
    vgroups = []
    bml_deform = bmsh.verts.layers.deform.verify()
    bml_texture = None
    has_sg_chunk = False
    for (cid, data) in creader:
        if cid == fmt.Chunks.Mesh.VERTS:
            reader = rw.read.PackedReader(data)
            vt_data = [reader.getv3fp() for _ in range(reader.int())]
        elif cid == fmt.Chunks.Mesh.FACES:
            s_6i = rw.read.PackedReader.prep('6I')
            reader = rw.read.PackedReader(data)
            faces_count = reader.int()
            fc_data = [reader.getp(s_6i) for _ in range(faces_count)]
        elif cid == fmt.Chunks.Mesh.MESHNAME:
            mesh_name = rw.read.PackedReader(data).gets()
            log.update(name=mesh_name)
        elif cid == fmt.Chunks.Mesh.SG:
            if not data:    # old object format
                continue
            has_sg_chunk = True
            sgroups = data.cast('I')

            def face_sg_impl(bmf, fidx, edict):
                sm_group = sgroups[fidx]
                # smoothing is stored in the edges
                # triangles should always be smoothed
                bmf.smooth = True
                if sm_group == sgfuncs[0]:
                    for bme in bmf.edges:
                        bme.smooth = False
                    return
                for eidx, bme in enumerate(bmf.edges):
                    prev = edict[bme.index]
                    if prev is None:
                        edict[bme.index] = (sm_group, eidx)
                    elif not sgfuncs[1](prev[0], sm_group, prev[1], eidx):
                        bme.smooth = False
            face_sg = face_sg_impl
        elif cid == fmt.Chunks.Mesh.NORMALS and prefs.object_split_normals:
            reader = rw.read.PackedReader(data)
            for face_index in range(faces_count):
                norm_1 = mathutils.Vector(reader.getv3fp()).normalized()
                norm_2 = mathutils.Vector(reader.getv3fp()).normalized()
                norm_3 = mathutils.Vector(reader.getv3fp()).normalized()
                split_normals.extend((norm_1, norm_3, norm_2))
        elif cid == fmt.Chunks.Mesh.SFACE:
            reader = rw.read.PackedReader(data)
            for _ in range(reader.getf('<H')[0]):
                name = reader.gets()
                s_faces.append((name, reader.getb(reader.int() * 4).cast('I')))
        elif cid == fmt.Chunks.Mesh.VMREFS:
            s_ii = rw.read.PackedReader.prep('2I')

            def read_vmref(reader):
                count = reader.byte()
                if count == 1:
                    return (reader.getp(s_ii),)  # fast path
                return [reader.getp(s_ii) for __ in range(count)]

            reader = rw.read.PackedReader(data)
            vm_refs = [read_vmref(reader) for _ in range(reader.int())]
        elif cid in (fmt.Chunks.Mesh.VMAPS1, fmt.Chunks.Mesh.VMAPS2):
            suppress_rename_warnings = {}
            reader = rw.read.PackedReader(data)
            for _ in range(reader.int()):
                name = reader.gets()
                if not name:
                    name = 'Texture'
                reader.skip(1)  # dim
                if cid == fmt.Chunks.Mesh.VMAPS2:
                    discon = reader.byte() != 0
                typ = reader.byte() & 0x3
                size = reader.int()
                if typ == fmt.VMapTypes.UVS:
                    new_name = renamemap.get(name.lower(), name)
                    if new_name != name:
                        if suppress_rename_warnings.get(name, None) != new_name:
                            log.warn(
                                text.warn.object_uv_renamed,
                                old=name,
                                new=new_name
                            )
                            suppress_rename_warnings[name] = new_name
                        name = new_name
                    bml = bmsh.loops.layers.uv.get(name)
                    if bml is None:
                        bml = bmsh.loops.layers.uv.new(name)
                        if utils.version.IS_28:
                            bml_texture = None
                        else:
                            bml_texture = bmsh.faces.layers.tex.new(name)
                    uvs = reader.getb(size * 8).cast('f')
                    if cid == fmt.Chunks.Mesh.VMAPS2:
                        reader.skip(size * 4)
                        if discon:
                            reader.skip(size * 4)
                    vmaps.append((typ, bml, uvs))
                elif typ == fmt.VMapTypes.WEIGHTS:  # weights
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
                            text.warn.object_zero_weight,
                            vmap=name
                        )
                    if cid == fmt.Chunks.Mesh.VMAPS2:
                        reader.skip(size * 4)
                        if discon:
                            reader.skip(size * 4)
                    vmaps.append((typ, vgi, wgs))
                else:
                    raise log.AppError(
                        text.error.object_bad_vmap,
                        log.props(type=typ)
                    )
        elif cid == fmt.Chunks.Mesh.FLAGS:
            mesh_flags = rw.read.PackedReader(data).getf('<B')[0]
            if mesh_flags & 0x4 and context.soc_sgroups:  # sgmask
                sgfuncs = (0, lambda ga, gb, ea, eb: ga == gb)
        elif cid == fmt.Chunks.Mesh.BBOX:
            pass  # blender automatically calculates bbox
        elif cid == fmt.Chunks.Mesh.OPTIONS:
            mesh_options = rw.read.PackedReader(data).getf('<2I')
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
                face = bmsh.faces.new(vertexes)
                face.smooth = True
                return face
            except ValueError:
                if len(set(vertexes)) < 3:
                    log.warn(text.warn.object_invalid_face)
                    return None
                if self.__next is None:
                    lvl = self.__level
                    if lvl > 100:
                        raise log.AppError(
                            text.error.object_many_duplicated_faces
                        )
                    nonlocal bad_vgroup
                    if bad_vgroup == -1:
                        bad_vgroup = len(bo_mesh.vertex_groups)
                        bo_mesh.vertex_groups.new(name=utils.BAD_VTX_GROUP_NAME)
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
    if face_sg or split_normals:
        bm_data.use_auto_smooth = True
        bm_data.auto_smooth_angle = math.pi
        if not utils.version.IS_28:
            bm_data.show_edge_sharp = True

    bo_mesh = bpy.data.objects.new(mesh_name, bm_data)
    if mesh_flags is not None:
        bo_mesh.data.xray.flags = mesh_flags
    if mesh_options is not None:
        bo_mesh.data.xray.options = mesh_options
    for vgroup in vgroups:
        bo_mesh.vertex_groups.new(name=vgroup)

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
        if not utils.version.IS_28:
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
                        text.warn.object_already_mat,
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

    if face_sg and not split_normals:
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
                        text.warn.object_already_used_mat,
                        face=fidx,
                        material=bmf.material_index,
                    )
                    continue
                bmf.material_index = midx
                if bml_texture is not None:
                    bmf[bml_texture].image = images[midx]
                assigned[fidx] = True

    if bad_vgroup != -1:
        msg = text.get_text(text.warn.object_duplicate_faces) + '. '
        if not context.split_by_materials:
            msg += text.get_text(text.warn.object_try_use_option)
            split_mesh_prop_name = utils.version.get_prop_name(
                ie.PropObjectMeshSplitByMaterials()
            )
            msg += ' "' + split_mesh_prop_name + '". '
        msg += text.get_text(text.warn.object_vert_group_created)
        log.warn(msg, vertex_group=bo_mesh.vertex_groups[bad_vgroup].name)

    if not has_sg_chunk:    # old object format
        for face in bmsh.faces:
            face.smooth = True

    bmsh.normal_update()
    bmsh.to_mesh(bm_data)

    if split_normals:
        bm_data.normals_split_custom_set(split_normals)

    return bo_mesh
