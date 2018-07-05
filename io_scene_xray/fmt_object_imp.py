import io
import math
import os.path

import bmesh
import bpy
import mathutils

from .xray_io import ChunkedReader, PackedReader
from .fmt_object import Chunks
from .plugin_prefs import PropObjectMeshSplitByMaterials
from .utils import BAD_VTX_GROUP_NAME, plugin_version_number, AppError
from .xray_motions import import_motions, MATRIX_BONE, MATRIX_BONE_INVERTED
from . import log


class ImportContext:
    def __init__(self, textures, soc_sgroups, import_motions, split_by_materials, operator):
        self.version = plugin_version_number()
        self.textures_folder = textures
        self.soc_sgroups = soc_sgroups
        self.import_motions = import_motions
        self.split_by_materials = split_by_materials
        self.operator = operator
        self.loaded_materials = None

    def before_import_file(self):
        self.loaded_materials = {}

    def image(self, relpath):
        relpath = relpath.lower().replace('\\', os.path.sep)
        if not self.textures_folder:
            result = bpy.data.images.new(os.path.basename(relpath), 0, 0)
            result.source = 'FILE'
            result.filepath = relpath + '.dds'
            return result

        filepath = os.path.abspath(os.path.join(self.textures_folder, relpath + '.dds'))
        result = None
        for i in bpy.data.images:
            if bpy.path.abspath(i.filepath) == filepath:
                result = i
                break
        if result is None:
            try:
                result = bpy.data.images.load(filepath)
            except RuntimeError as ex:  # e.g. 'Error: Cannot read ...'
                log.warn(ex)
                result = bpy.data.images.new(os.path.basename(relpath), 0, 0)
                result.source = 'FILE'
                result.filepath = filepath
        return result


_S_FFF = PackedReader.prep('fff')


def read_v3f(packed_reader):
    vec = packed_reader.getp(_S_FFF)
    return vec[0], vec[2], vec[1]


def _cop_sgfunc(group_a, group_b, edge_a, edge_b):
    bfa, bfb = bool(group_a & 0x8), bool(group_b & 0x8)  # test backface-s
    if bfa != bfb:
        return False

    def is_soft(group, backface, edge):
        return (group & (4, 2, 1)[(4 - edge) % 3 if backface else edge]) == 0

    return is_soft(group_a, bfa, edge_a) and is_soft(group_b, bfb, edge_b)


_SHARP = 0xffffffff
_MIN_WEIGHT = 0.0002

@log.with_context(name='mesh')
def _import_mesh(context, creader, renamemap):
    ver = creader.nextf(Chunks.Mesh.VERSION, 'H')[0]
    if ver != 0x11:
        raise AppError('unsupported MESH format version', log.props(version=ver))
    mesh_name = None
    mesh_flags = None
    mesh_options = None
    bmsh = bmesh.new()
    sgfuncs = (_SHARP, lambda ga, gb, ea, eb: ga == gb) if context.soc_sgroups else (_SHARP, _cop_sgfunc)
    vt_data = ()
    fc_data = ()

    face_sg = None
    s_faces = []
    vm_refs = ()
    vmaps = []
    vgroups = []
    bml_deform = bmsh.verts.layers.deform.verify()
    bml_texture = None
    for (cid, data) in creader:
        if cid == Chunks.Mesh.VERTS:
            reader = PackedReader(data)
            vt_data = [read_v3f(reader) for _ in range(reader.int())]
        elif cid == Chunks.Mesh.FACES:
            s_6i = PackedReader.prep('IIIIII')
            reader = PackedReader(data)
            count = reader.int()
            fc_data = [reader.getp(s_6i) for _ in range(count)]
        elif cid == Chunks.Mesh.MESHNAME:
            mesh_name = PackedReader(data).gets()
            log.update(name=mesh_name)
        elif cid == Chunks.Mesh.SG:
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
        elif cid == Chunks.Mesh.SFACE:
            reader = PackedReader(data)
            for _ in range(reader.getf('H')[0]):
                name = reader.gets()
                s_faces.append((name, reader.getb(reader.int() * 4).cast('I')))
        elif cid == Chunks.Mesh.VMREFS:
            s_ii = PackedReader.prep('II')

            def read_vmref(reader):
                count = reader.byte()
                if count == 1:
                    return (reader.getp(s_ii),)  # fast path
                return [reader.getp(s_ii) for __ in range(count)]

            reader = PackedReader(data)
            vm_refs = [read_vmref(reader) for _ in range(reader.int())]
        elif cid == Chunks.Mesh.VMAPS1 or cid == Chunks.Mesh.VMAPS2:
            suppress_rename_warnings = {}
            reader = PackedReader(data)
            for _ in range(reader.int()):
                name = reader.gets()
                reader.skip(1)  # dim
                if cid == Chunks.Mesh.VMAPS2:
                    discon = reader.byte() != 0
                typ = reader.byte() & 0x3
                size = reader.int()
                if typ == 0:
                    new_name = renamemap.get(name.lower(), name)
                    if new_name != name:
                        if suppress_rename_warnings.get(name, None) != new_name:
                            log.warn('texture VMap has been renamed', old=name, new=new_name)
                            suppress_rename_warnings[name] = new_name
                        name = new_name
                    bml = bmsh.loops.layers.uv.get(name)
                    if bml is None:
                        bml = bmsh.loops.layers.uv.new(name)
                        bml_texture = bmsh.faces.layers.tex.new(name)
                    uvs = reader.getb(size * 8).cast('f')
                    if cid == Chunks.Mesh.VMAPS2:
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
                        log.warn('weight VMap has values that are close to zero', vmap=name)
                    if cid == Chunks.Mesh.VMAPS2:
                        reader.skip(size * 4)
                        if discon:
                            reader.skip(size * 4)
                    vmaps.append((typ, vgi, wgs))
                else:
                    raise AppError('unknown vmap type', log.props(type=typ))
        elif cid == Chunks.Mesh.FLAGS:
            mesh_flags = PackedReader(data).getf('B')[0]
            if mesh_flags & 0x4:  # sgmask
                sgfuncs = (0, lambda ga, gb, ea, eb: bool(ga & gb))
        elif cid == Chunks.Mesh.BBOX:
            pass  # blender automatically calculates bbox
        elif cid == Chunks.Mesh.OPTIONS:
            mesh_options = PackedReader(data).getf('II')
        elif cid == Chunks.Mesh.NOT_USED_0:
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
            vertexes = (self._vtx(fr, i0), self._vtx(fr, i1), self._vtx(fr, i2))
            try:
                return bmsh.faces.new(vertexes)
            except ValueError:
                if len(set(vertexes)) < 3:
                    log.warn('invalid face found')
                    return None
                if self.__next is None:
                    lvl = self.__level
                    if lvl > 100:
                        raise AppError('too many duplicated polygons')
                    nonlocal bad_vgroup
                    if bad_vgroup == -1:
                        bad_vgroup = len(bo_mesh.vertex_groups)
                        bo_mesh.vertex_groups.new(BAD_VTX_GROUP_NAME)
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
            context.loaded_materials[name] = bmat = bpy.data.materials.new(name)
            bmat.xray.version = context.version
        midx = len(bm_data.materials)
        bm_data.materials.append(bmat)
        images.append(bmat.active_texture.image if bmat.active_texture else None)
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
                PropObjectMeshSplitByMaterials()[1].get('name')
            )
        log.warn(msg)

    bmsh.normal_update()
    bmsh.to_mesh(bm_data)

    return bo_mesh


def _get_real_bone_shape():
    result = bpy.data.objects.get('real_bone_shape')
    if result is None:
        result = bpy.data.objects.new('real_bone_shape', None)
        result.empty_draw_type = 'SPHERE'
    return result


def _create_bone(context, bpy_arm_obj, name, parent, vmap, offset, rotate, length, renamemap):
    bpy_armature = bpy_arm_obj.data
    if name != vmap:
        ex = renamemap.get(vmap, None)
        if ex is None:
            log.warn('bone VMap: will be renamed', vmap=vmap, name=name)
        elif ex != name:
            log.warn('bone VMap: is already renamed', vmap=vmap, name1=ex, name2=name)
        renamemap[vmap] = name
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        bpy_bone = bpy_armature.edit_bones.new(name=name)
        rot = mathutils.Euler((-rotate[0], -rotate[1], -rotate[2]), 'YXZ').to_matrix().to_4x4()
        mat = mathutils.Matrix.Translation(offset) * rot * MATRIX_BONE
        if parent:
            bpy_bone.parent = bpy_armature.edit_bones.get(parent, None)
            if bpy_bone.parent:
                mat = bpy_bone.parent.matrix * MATRIX_BONE_INVERTED * mat
            else:
                log.warn('bone parent isn\'t found', bone=name, parent=parent)
        bpy_bone.tail.y = 0.02
        bpy_bone.matrix = mat
        name = bpy_bone.name
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')
    pose_bone = bpy_arm_obj.pose.bones[name]
    if context.operator.shaped_bones:
        pose_bone.custom_shape = _get_real_bone_shape()
    bpy_bone = bpy_armature.bones[name]
    xray = bpy_bone.xray
    xray.version = context.version
    xray.length = length
    return bpy_bone


def _safe_assign_enum_property(obj, pname, val, desc):
    defval = getattr(obj, pname)
    try:
        setattr(obj, pname, val)
    except TypeError:
        log.warn(
            'unsupported %s %s, using default' % (desc, pname),
            value=val,
            default=defval,
        )


@log.with_context(name='bone')
def _import_bone(context, creader, bpy_arm_obj, renamemap):
    ver = creader.nextf(Chunks.Bone.VERSION, 'H')[0]
    if ver != 0x2:
        raise AppError('unsupported BONE format version', log.props(version=ver))

    reader = PackedReader(creader.next(Chunks.Bone.DEF))
    name = reader.gets()
    log.update(name=name)
    parent = reader.gets()
    vmap = reader.gets()

    reader = PackedReader(creader.next(Chunks.Bone.BIND_POSE))
    offset = read_v3f(reader)
    rotate = read_v3f(reader)
    length = reader.getf('f')[0]

    bpy_bone = _create_bone(
        context, bpy_arm_obj,
        name, parent,
        vmap,
        offset, rotate, length,
        renamemap,
    )
    xray = bpy_bone.xray
    for (cid, data) in creader:
        if cid == Chunks.Bone.DEF:
            def2 = PackedReader(data).gets()
            if name != def2:
                log.warn('Not supported yet! bone name != bone def2', name=name, def2=def2)
        elif cid == Chunks.Bone.MATERIAL:
            xray.gamemtl = PackedReader(data).gets()
        elif cid == Chunks.Bone.SHAPE:
            reader = PackedReader(data)
            _safe_assign_enum_property(xray.shape, 'type', str(reader.getf('H')[0]), 'bone shape')
            xray.shape.flags = reader.getf('H')[0]
            xray.shape.box_rot = reader.getf('fffffffff')
            xray.shape.box_trn = reader.getf('fff')
            xray.shape.box_hsz = reader.getf('fff')
            xray.shape.sph_pos = reader.getf('fff')
            xray.shape.sph_rad = reader.getf('f')[0]
            xray.shape.cyl_pos = reader.getf('fff')
            xray.shape.cyl_dir = reader.getf('fff')
            xray.shape.cyl_hgh = reader.getf('f')[0]
            xray.shape.cyl_rad = reader.getf('f')[0]
            xray.shape.set_curver()
        elif cid == Chunks.Bone.IK_JOINT:
            reader = PackedReader(data)
            pose_bone = bpy_arm_obj.pose.bones[name]
            value = str(reader.int())
            _safe_assign_enum_property(xray.ikjoint, 'type', value, 'bone ikjoint')
            pose_bone.use_ik_limit_x = True
            pose_bone.ik_min_x, pose_bone.ik_max_x = reader.getf('ff')
            xray.ikjoint.lim_x_spr, xray.ikjoint.lim_x_dmp = reader.getf('ff')
            pose_bone.use_ik_limit_y = True
            pose_bone.ik_min_y, pose_bone.ik_max_y = reader.getf('ff')
            xray.ikjoint.lim_y_spr, xray.ikjoint.lim_y_dmp = reader.getf('ff')
            pose_bone.use_ik_limit_z = True
            pose_bone.ik_min_z, pose_bone.ik_max_z = reader.getf('ff')
            xray.ikjoint.lim_z_spr, xray.ikjoint.lim_z_dmp = reader.getf('ff')
            xray.ikjoint.spring = reader.getf('f')[0]
            xray.ikjoint.damping = reader.getf('f')[0]
        elif cid == Chunks.Bone.MASS_PARAMS:
            reader = PackedReader(data)
            xray.mass.value = reader.getf('f')[0]
            xray.mass.center = read_v3f(reader)
        elif cid == Chunks.Bone.IK_FLAGS:
            xray.ikflags = PackedReader(data).int()
        elif cid == Chunks.Bone.BREAK_PARAMS:
            reader = PackedReader(data)
            xray.breakf.force = reader.getf('f')[0]
            xray.breakf.torque = reader.getf('f')[0]
        elif cid == Chunks.Bone.FRICTION:
            xray.friction = PackedReader(data).getf('f')[0]
        else:
            log.debug('unknown chunk', cid=cid)

def _is_compatible_texture(texture, filepart):
    image = getattr(texture, 'image', None)
    if image is None:
        return False
    if filepart not in image.filepath:
        return False
    return True

def _import_main(fpath, context, creader):
    object_name = os.path.basename(fpath.lower())

    bpy_arm_obj = None
    renamemap = {}
    meshes_data = None

    unread_chunks = []

    for (cid, data) in creader:
        if cid == Chunks.Object.VERSION:
            reader = PackedReader(data)
            ver = reader.getf('H')[0]
            if ver != 0x10:
                raise AppError('unsupported OBJECT format version', log.props(version=ver))
        elif cid == Chunks.Object.MESHES:
            meshes_data = data
        elif (cid == Chunks.Object.SURFACES) or (cid == Chunks.Object.SURFACES1) or \
            (cid == Chunks.Object.SURFACES2):
            reader = PackedReader(data)
            surfaces_count = reader.int()
            if cid == Chunks.Object.SURFACES:
                try:
                    xrlc_reader = PackedReader(creader.next(Chunks.Object.SURFACES_XRLC))
                    xrlc_shaders = [xrlc_reader.gets() for _ in range(surfaces_count)]
                except:
                    xrlc_shaders = ['default' for _ in range(surfaces_count)]
            for surface_index in range(surfaces_count):
                if cid == Chunks.Object.SURFACES:
                    name = reader.gets()
                    eshader = reader.gets()
                    flags = reader.getf('B')[0]
                    reader.skip(4 + 4)    # fvf and TCs count
                    texture = reader.gets()
                    vmap = reader.gets()
                    if texture != vmap:
                        old_object_format = False
                        renamemap[vmap.lower()] = vmap
                    else:    # old format (Objects\Rainbow\lest.object)
                        old_object_format = True
                        vmap = 'UVMap'
                    gamemtl = 'default'
                    cshader = xrlc_shaders[surface_index]
                else:
                    name = reader.gets()
                    eshader = reader.gets()
                    cshader = reader.gets()
                    gamemtl = reader.gets() if cid == Chunks.Object.SURFACES2 else 'default'
                    texture = reader.gets()
                    vmap = reader.gets()
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
                        all_empty_slots = all(not slot for slot in material.texture_slots)
                        if all_empty_slots:
                            bpy_material = material
                            break

                    ts_found = False
                    for slot in material.texture_slots:
                        if not slot:
                            continue
                        if slot.uv_layer != vmap:
                            continue
                        if not _is_compatible_texture(slot.texture, tx_filepart):
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
                            or not _is_compatible_texture(bpy_texture, tx_filepart):
                            bpy_texture = bpy.data.textures.new(texture, type='IMAGE')
                            bpy_texture.image = context.image(texture)
                            bpy_texture.use_preview_alpha = True
                        bpy_texture_slot = bpy_material.texture_slots.add()
                        bpy_texture_slot.texture = bpy_texture
                        bpy_texture_slot.texture_coords = 'UV'
                        bpy_texture_slot.uv_layer = vmap
                        bpy_texture_slot.use_map_color_diffuse = True
                        bpy_texture_slot.use_map_alpha = True
                context.loaded_materials[name] = bpy_material
        elif (cid == Chunks.Object.BONES) or (cid == Chunks.Object.BONES1):
            if cid == Chunks.Object.BONES:
                reader = PackedReader(data)
                bones_count = reader.int()
                if not bones_count:
                    continue    # Do not create an armature if zero bones
            if bpy and (bpy_arm_obj is None):
                bpy_armature = bpy.data.armatures.new(object_name)
                bpy_armature.use_auto_ik = True
                bpy_armature.draw_type = 'STICK'
                bpy_arm_obj = bpy.data.objects.new(object_name, bpy_armature)
                bpy_arm_obj.show_x_ray = True
                bpy.context.scene.objects.link(bpy_arm_obj)
                bpy.context.scene.objects.active = bpy_arm_obj
            if cid == Chunks.Object.BONES:
                for _ in range(bones_count):
                    name, parent, vmap = reader.gets(), reader.gets(), reader.gets()
                    offset, rotate, length = read_v3f(reader), read_v3f(reader), reader.getf('f')[0]
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
                    xray.ikjoint.lim_x_spr, xray.ikjoint.lim_x_dmp = 1, 1
                    xray.ikjoint.lim_y_spr, xray.ikjoint.lim_y_dmp = 1, 1
                    xray.ikjoint.lim_z_spr, xray.ikjoint.lim_z_dmp = 1, 1
                    xray.ikjoint.spring = 1
                    xray.ikjoint.damping = 1
            else:
                for (_, bdat) in ChunkedReader(data):
                    _import_bone(context, ChunkedReader(bdat), bpy_arm_obj, renamemap)
            bpy.ops.object.mode_set(mode='EDIT')
            try:
                if context.operator.shaped_bones:
                    bones = bpy_armature.edit_bones
                    lenghts = [0] * len(bones)
                    for i, bone in enumerate(bones):
                        min_rad_sq = math.inf
                        for j, bone1 in enumerate(bones):
                            if j == i:
                                continue
                            rad_sq = (bone1.head - bone.head).length_squared
                            if rad_sq < min_rad_sq:
                                min_rad_sq = rad_sq
                        lenghts[i] = math.sqrt(min_rad_sq)
                    for bone, length in zip(bones, lenghts):
                        bone.length = min(max(length * 0.4, 0.01), 0.1)
            finally:
                bpy.ops.object.mode_set(mode='OBJECT')
            for bone in bpy_arm_obj.pose.bones:
                bone.rotation_mode = 'ZXY'
        elif (cid == Chunks.Object.PARTITIONS0) or (cid == Chunks.Object.PARTITIONS1):
            bpy.context.scene.objects.active = bpy_arm_obj
            bpy.ops.object.mode_set(mode='POSE')
            try:
                reader = PackedReader(data)
                for _partition_idx in range(reader.int()):
                    bpy.ops.pose.group_add()
                    bone_group = bpy_arm_obj.pose.bone_groups.active
                    bone_group.name = reader.gets()
                    for _bone_idx in range(reader.int()):
                        name = reader.gets() if cid == Chunks.Object.PARTITIONS1 else reader.int()
                        bpy_arm_obj.pose.bones[name].bone_group = bone_group
            finally:
                bpy.ops.object.mode_set(mode='OBJECT')
        elif cid == Chunks.Object.MOTIONS:
            if not context.import_motions:
                continue
            reader = PackedReader(data)
            import_motions(reader, bpy_arm_obj)
        elif cid == Chunks.Object.LIB_VERSION:
            pass  # skip obsolete chunk
        else:
            unread_chunks.append((cid, data))

    mesh_objects = []
    for (_, mdat) in ChunkedReader(meshes_data):
        mesh = _import_mesh(context, ChunkedReader(mdat), renamemap)

        if bpy_arm_obj:
            bpy_armmod = mesh.modifiers.new(name='Armature', type='ARMATURE')
            bpy_armmod.object = bpy_arm_obj
            mesh.parent = bpy_arm_obj

        mesh_objects.append(mesh)
        bpy.context.scene.objects.link(mesh)

    bpy_obj = bpy_arm_obj
    if bpy_obj is None:
        if len(mesh_objects) == 1:
            bpy_obj = mesh_objects[0]
            bpy_obj.name = object_name
        else:
            bpy_obj = bpy.data.objects.new(object_name, None)
            for mesh in mesh_objects:
                mesh.parent = bpy_obj
            bpy.context.scene.objects.link(bpy_obj)

    bpy_obj.xray.version = context.version
    bpy_obj.xray.isroot = True
    for (cid, data) in unread_chunks:
        if cid == Chunks.Object.TRANSFORM:
            reader = PackedReader(data)
            pos = read_v3f(reader)
            rot = read_v3f(reader)
            bpy_obj.matrix_basis *= mathutils.Matrix.Translation(pos) \
                * mathutils.Euler(rot, 'YXZ').to_matrix().to_4x4()
        elif cid == Chunks.Object.FLAGS:
            length_data = len(data)
            if length_data == 4:
                bpy_obj.xray.flags = PackedReader(data).int()
            elif length_data == 1:    # old object format
                bpy_obj.xray.flags = PackedReader(data).getf('B')[0]
        elif cid == Chunks.Object.USERDATA:
            bpy_obj.xray.userdata = \
                PackedReader(data).gets(onerror=lambda e: log.warn('bad userdata', error=e))
        elif cid == Chunks.Object.LOD_REF:
            bpy_obj.xray.lodref = PackedReader(data).gets()
        elif cid == Chunks.Object.REVISION:
            reader = PackedReader(data)
            bpy_obj.xray.revision.owner = reader.gets()
            bpy_obj.xray.revision.ctime = reader.int()
            bpy_obj.xray.revision.moder = reader.gets()
            bpy_obj.xray.revision.mtime = reader.int()
        elif cid == Chunks.Object.MOTION_REFS:
            mrefs = bpy_obj.xray.motionrefs_collection
            for mref in PackedReader(data).gets().split(','):
                mrefs.add().name = mref
        elif cid == Chunks.Object.SMOTIONS3:
            reader = PackedReader(data)
            mrefs = bpy_obj.xray.motionrefs_collection
            for _ in range(reader.int()):
                mrefs.add().name = reader.gets()
        else:
            log.debug('unknown chunk', cid=cid)


def _import(fpath, context, reader):
    for (cid, data) in reader:
        if cid == Chunks.Object.MAIN:
            _import_main(fpath, context, ChunkedReader(data))
        else:
            log.debug('unknown chunk', cid=cid)


@log.with_context(name='file')
def import_file(fpath, context):
    log.update(path=fpath)
    with io.open(fpath, 'rb') as file:
        _import(fpath, context, ChunkedReader(memoryview(file.read())))
