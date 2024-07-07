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


_SHARP_MAYA = 0xffffffff
_SHARP_MAX = 0x0
_MIN_WEIGHT = 0.0002
DEFAULT_UV_NAME = 'Texture'

_soc_sgfunc = lambda group_a, group_b, edge_a, edge_b: group_a == group_b


def is_soft(group, backface, edge):
    return (group & (4, 2, 1)[(4 - edge) % 3 if backface else edge]) == 0


def _cop_sgfunc(group_a, group_b, edge_a, edge_b):
    bfa, bfb = bool(group_a & 0x8), bool(group_b & 0x8)    # test backface-s
    if bfa != bfb:
        return False

    return is_soft(group_a, bfa, edge_a) and is_soft(group_b, bfb, edge_b)


def face_sg_impl(smooth_groups, sg_fun, sharp, bm_face, face_index, edict):
    smooth_group = smooth_groups[face_index]

    # smoothing is stored in the edges
    # triangles should always be smoothed
    bm_face.smooth = True

    if smooth_group == sharp:
        for bm_edge in bm_face.edges:
            bm_edge.smooth = False

    else:
        for edge_index, bm_edge in enumerate(bm_face.edges):
            prev = edict[bm_edge.index]

            if prev is None:
                edict[bm_edge.index] = (smooth_group, edge_index)

            elif not sg_fun(prev[0], smooth_group, prev[1], edge_index):
                bm_edge.smooth = False


def read_vertex_map_reference(reader, struct_2i):
    count = reader.byte()

    if count == 1:
        return (reader.getp(struct_2i), )    # fast path

    return [reader.getp(struct_2i) for __ in range(count)]


@log.with_context(name='mesh')
def import_mesh(context, chunked_reader, renamemap, file_name):

    # mesh version
    ver_chunk = chunked_reader.next(fmt.Chunks.Mesh.VERSION)
    ver_reader = rw.read.PackedReader(ver_chunk)
    ver = ver_reader.getf('<H')[0]

    # check version
    if ver != fmt.CURRENT_MESH_VERSION:
        raise log.AppError(
            text.error.object_unsupport_mesh_ver,
            log.props(version=ver)
        )

    mesh_name = None
    mesh_flags = None
    mesh_options = None

    vt_data = None
    fc_data = None
    vm_refs = None

    face_sg = None
    bml_texture = None

    has_sg_chunk = False
    has_multiple_uvs = False

    surface_faces = []
    split_normals = []
    vmaps = []
    vgroups = []

    sharp = _SHARP_MAYA
    use_normals = utils.version.get_preferences().object_split_normals

    # choose smoothing groups function
    if context.soc_sgroups:
        sg_fun = _soc_sgfunc
    else:
        sg_fun = _cop_sgfunc

    # create bmesh
    bmsh = bmesh.new()
    bml_deform = bmsh.verts.layers.deform.verify()

    # read chunks
    for chunk_id, chunk_data in chunked_reader:

        # vertices
        if chunk_id == fmt.Chunks.Mesh.VERTS:
            reader = rw.read.PackedReader(chunk_data)
            verts_count = reader.uint32()
            vt_data = reader.getverts(verts_count)

        # triangles
        elif chunk_id == fmt.Chunks.Mesh.FACES:
            reader = rw.read.PackedReader(chunk_data)
            faces_count = reader.uint32()
            fc_data = reader.get_array('I', faces_count, vec_len=6)

        # mesh name
        elif chunk_id == fmt.Chunks.Mesh.MESHNAME:
            reader = rw.read.PackedReader(chunk_data)
            mesh_name = reader.gets()
            log.update(name=mesh_name)

        # smoothing groups
        elif chunk_id == fmt.Chunks.Mesh.SG:

            if not chunk_data:    # old object format
                continue

            has_sg_chunk = True
            sgroups = chunk_data.cast('I')
            face_sg = face_sg_impl

        # split normals
        elif chunk_id == fmt.Chunks.Mesh.NORMALS and use_normals:
            reader = rw.read.PackedReader(chunk_data)
            for face_index in range(faces_count):
                norm_1 = mathutils.Vector(reader.getv3fp()).normalized()
                norm_2 = mathutils.Vector(reader.getv3fp()).normalized()
                norm_3 = mathutils.Vector(reader.getv3fp()).normalized()
                split_normals.extend((norm_1, norm_3, norm_2))

        # surfaces
        elif chunk_id == fmt.Chunks.Mesh.SFACE:
            reader = rw.read.PackedReader(chunk_data)
            surface_count = reader.getf('<H')[0]
            for _ in range(surface_count):
                name = reader.gets()
                surf_faces_count = reader.uint32()
                face_indices = reader.getb(surf_faces_count * 4).cast('I')
                surface_faces.append((name, face_indices))

        # vertex map references
        elif chunk_id == fmt.Chunks.Mesh.VMREFS:
            struct_2i = rw.read.PackedReader.prep('2I')
            reader = rw.read.PackedReader(chunk_data)
            vertex_map_count = reader.uint32()
            vm_refs = [
                read_vertex_map_reference(reader, struct_2i)
                for _ in range(vertex_map_count)
            ]

        # vertex maps
        elif chunk_id in (fmt.Chunks.Mesh.VMAPS1, fmt.Chunks.Mesh.VMAPS2):
            suppress_rename_warnings = {}
            zero_maps = set()
            reader = rw.read.PackedReader(chunk_data)
            vmap_count = reader.uint32()

            for _ in range(vmap_count):
                name = reader.gets()
                if not name:
                    name = DEFAULT_UV_NAME
                reader.skip(1)    # dim
                if chunk_id == fmt.Chunks.Mesh.VMAPS2:
                    discon = reader.byte() != 0
                typ = reader.byte() & 0x3
                size = reader.uint32()

                # uvs
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
                        if len(bmsh.loops.layers.uv):
                            bml = bmsh.loops.layers.uv[0]
                            has_multiple_uvs = True
                        else:
                            bml = bmsh.loops.layers.uv.new(name)
                        if utils.version.IS_28:
                            bml_texture = None
                        else:
                            bml_texture = bmsh.faces.layers.tex.new(name)
                    uvs = reader.getb(size * 8).cast('f')
                    if chunk_id == fmt.Chunks.Mesh.VMAPS2:
                        reader.skip(size * 4)
                        if discon:
                            reader.skip(size * 4)
                    vmaps.append((typ, bml, uvs))

                # weights
                elif typ == fmt.VMapTypes.WEIGHTS:
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
                        zero_maps.add(name)
                    if chunk_id == fmt.Chunks.Mesh.VMAPS2:
                        reader.skip(size * 4)
                        if discon:
                            reader.skip(size * 4)
                    vmaps.append((typ, vgi, wgs))

                else:
                    raise log.AppError(
                        text.error.object_bad_vmap,
                        log.props(type=typ)
                    )

            # zero weights report
            if zero_maps:
                zero_maps = list(zero_maps)
                zero_maps.sort()
                if len(zero_maps) == 1:
                    log.warn(
                        text.warn.object_zero_weight,
                        vmaps=zero_maps[0]
                    )
                else:
                    log.warn(
                        text.warn.object_zero_weight,
                        count='[{}x]'.format(len(zero_maps)),
                        vmaps=zero_maps
                    )

        # mesh flags
        elif chunk_id == fmt.Chunks.Mesh.FLAGS:
            reader = rw.read.PackedReader(chunk_data)
            mesh_flags = reader.getf('<B')[0]

            if mesh_flags & 0x4 and context.soc_sgroups:    # sgmask
                sharp = _SHARP_MAX
                sg_fun = _soc_sgfunc

        # bounding box
        elif chunk_id == fmt.Chunks.Mesh.BBOX:
            pass    # blender automatically calculates bbox

        # mesh options
        elif chunk_id == fmt.Chunks.Mesh.OPTIONS:
            reader = rw.read.PackedReader(chunk_data)
            mesh_options = reader.getf('<2I')

        # not used chunk
        elif chunk_id == fmt.Chunks.Mesh.NOT_USED_0:
            pass

        # unknown chunk
        else:
            log.debug('unknown chunk', chunk_id=chunk_id)

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
                    if vmap[0] == fmt.VMapTypes.UVS:
                        vi *= 2
                        vd = vmap[2]
                        bmf.loops[i][vmap[1]].uv = (vd[vi], 1 - vd[vi + 1])
            return bmf

        def _vtx(self, _fr, _i):
            raise NotImplementedError

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
                        bad_vgroup = len(bpy_obj.vertex_groups)
                        bpy_obj.vertex_groups.new(name=utils.BAD_VTX_GROUP_NAME)
                    self.__next = self.__class__(lvl + 1, badvg=bad_vgroup)
                return self.__next._mkf(fr, i0, i1, i2)

    class LocalSimple(LocalAbstract):    # fastpath
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
                if vmap[0] == fmt.VMapTypes.WEIGHTS:
                    vkey.append((vmap[1], vmap[2][vei]))
            vkey = tuple(vkey)

            vertex = self.__verts.get(vkey, None)
            if vertex is None:
                self.__verts[vkey] = vertex = bmsh.verts.new(vt_data[vidx])
                for vl, vv in vkey[1:]:
                    vertex[bml_deform][vl] = vv
            self._vgvtx(vertex)
            return vertex

    # create mesh
    bm_data = bpy.data.meshes.new(mesh_name)
    utils.stats.created_msh()

    # set smooth settings
    bm_data.use_auto_smooth = True
    bm_data.auto_smooth_angle = math.pi
    if not utils.version.IS_28:
        bm_data.show_edge_sharp = True

    # choose object name
    if file_name:
        obj_name = file_name
    else:
        obj_name = mesh_name

    # create object
    bpy_obj = bpy.data.objects.new(obj_name, bm_data)
    utils.stats.created_obj()

    # set flags
    if mesh_flags is not None:
        bpy_obj.data.xray.flags = mesh_flags

    # set options
    if mesh_options is not None:
        bpy_obj.data.xray.options = mesh_options

    # create vertex groups
    for group_name in vgroups:
        bpy_obj.vertex_groups.new(name=group_name)

    # create materials
    f_facez = []
    images = []

    for name, faces in surface_faces:

        # search material
        bpy_mat = context.loaded_materials.get(name)

        # create material
        if bpy_mat is None:
            context.loaded_materials[name] = bpy_mat = \
                bpy.data.materials.new(name)
            bpy_mat.xray.version = context.version
            utils.stats.created_mat()

        material_index = len(bm_data.materials)
        bm_data.materials.append(bpy_mat)
        f_facez.append((faces, material_index))

        if not utils.version.IS_28:
            images.append(
                bpy_mat.active_texture.image
                if bpy_mat.active_texture else None
            )

    local_class = LocalComplex if vgroups else LocalSimple

    bmfaces = [None] * len(fc_data)

    # create faces splitted by materials
    if context.split_by_materials:
        for faces, mat_index in f_facez:
            local = local_class()
            for face_index in faces:
                bmf = bmfaces[face_index]
                if bmf is not None:
                    log.warn(
                        text.warn.object_already_mat,
                        face=face_index,
                        material=bmf.material_index,
                    )
                    continue
                bmfaces[face_index] = bmf = local.mkface(face_index)
                if bmf is None:
                    continue
                bmf.material_index = mat_index
                if bml_texture is not None:
                    bmf[bml_texture].image = images[mat_index]

    # create faces
    local = local_class()
    for face_index, bmf in enumerate(bmfaces):
        if bmf is not None:
            continue    # already instantiated
        bmfaces[face_index] = local.mkface(face_index)

    # set smoothing
    if face_sg and not split_normals:
        bmsh.edges.index_update()
        edict = [None] * len(bmsh.edges)
        for face_index, bmf in enumerate(bmfaces):
            if bmf is None:
                continue
            face_sg(sgroups, sg_fun, sharp, bmf, face_index, edict)

    # assign materials
    if not context.split_by_materials:
        assigned = [False] * len(bmfaces)
        for faces, mat_index in f_facez:
            for face_index in faces:
                bmf = bmfaces[face_index]
                if bmf is None:
                    continue
                if assigned[face_index]:
                    log.warn(
                        text.warn.object_already_used_mat,
                        face=face_index,
                        material=bmf.material_index,
                    )
                    continue
                bmf.material_index = mat_index
                if bml_texture is not None:
                    bmf[bml_texture].image = images[mat_index]
                assigned[face_index] = True

    # duplicate faces report
    if bad_vgroup != -1:
        msg = text.get_tip(text.warn.object_duplicate_faces) + '. '
        if not context.split_by_materials:
            msg += text.get_tip(text.warn.object_try_use_option)
            split_mesh_prop_name = utils.version.get_prop_name(
                ie.PropObjectMeshSplitByMaterials()
            )
            msg += ' "' + split_mesh_prop_name + '". '
        msg += text.get_tip(text.warn.object_vert_group_created)
        log.warn(msg, vertex_group=bpy_obj.vertex_groups[bad_vgroup].name)

    # convert bmesh to bpy-mesh
    bmsh.normal_update()
    bmsh.to_mesh(bm_data)

    # rename uv-map
    if has_multiple_uvs:
        bm_data.uv_layers[0].name = DEFAULT_UV_NAME

    # set split normals
    if split_normals:
        bm_data.normals_split_custom_set(split_normals)

    return bpy_obj
