# standart modules
import time
import math

# blender modules
import bpy
import bmesh
import mathutils

# addon modules
from .. import fmt
from ... import omf
from ... import motions
from .... import text
from .... import rw
from .... import log
from .... import utils


FIRST_SHADER = 0


def write_verts_1l(vertices_writer, vertices, norm_coef=1):
    for vertex in vertices:
        vertices_writer.putv3f(vertex[1])    # coord
        vertices_writer.putv3f((
            norm_coef * vertex[2][0],
            norm_coef * vertex[2][1],
            norm_coef * vertex[2][2]
        ))    # normal
        vertices_writer.putv3f(vertex[3])    # tangent
        vertices_writer.putv3f(vertex[4])    # bitangent
        vertices_writer.putf('<2f', *vertex[5])    # uv
        vertices_writer.putf('<I', vertex[6][0][0])


def write_verts_2l(vertices_writer, vertices, norm_coef=1):
    for vertex in vertices:
        weights = vertex[6]
        if len(weights) > 2:
            weights = utils.mesh.weights_top_two(weights)
        weight = 0
        # 2-link vertex
        if len(weights) == 2:
            first = True
            weight0 = 0
            for vgi, vert_weight in weights:
                vertices_writer.putf('<H', vgi)
                if first:
                    weight0 = vert_weight
                    first = False
                else:
                    weight = 1 - (weight0 / (weight0 + vert_weight))
        # 1-link vertex
        elif len(weights) == 1:
            vertices_writer.putf(
                '<2H',
                weights[0][0],
                weights[0][0]
            )
        else:
            raise Exception('oops: {} {}'.format(
                len(weights),
                weights.keys()
            ))
        # write vertex data
        vertices_writer.putv3f(vertex[1])    # coord
        vertices_writer.putv3f((
            norm_coef * vertex[2][0],
            norm_coef * vertex[2][1],
            norm_coef * vertex[2][2]
        ))    # normal
        vertices_writer.putv3f(vertex[3])    # tangent
        vertices_writer.putv3f(vertex[4])    # bitangent
        vertices_writer.putf('<f', weight)    # weight
        vertices_writer.putf('<2f', *vertex[5])    # uv


def _export_child(
        root_obj,
        bpy_obj,
        chunked_writer,
        context,
        vertex_groups_map
    ):

    modifiers = [
        mod
        for mod in bpy_obj.modifiers
            if mod.type != 'ARMATURE' and mod.show_viewport
    ]

    loc_space, rot_space, scl_space = utils.ie.get_object_world_matrix(root_obj)
    mesh = utils.mesh.convert_object_to_space_bmesh(
        bpy_obj,
        loc_space,
        rot_space,
        scl_space,
        mods=modifiers
    )

    bbox = utils.mesh.calculate_mesh_bbox(mesh.verts)
    bsphere = utils.mesh.calculate_mesh_bsphere(bbox, mesh.verts)
    bmesh.ops.triangulate(mesh, faces=mesh.faces)
    bpy_mesh = bpy.data.meshes.new('.export-ogf')
    bpy_mesh.use_auto_smooth = bpy_obj.data.use_auto_smooth
    bpy_mesh.auto_smooth_angle = bpy_obj.data.auto_smooth_angle
    mesh.to_mesh(bpy_mesh)

    # write header chunk
    header_writer = rw.write.PackedWriter()
    header_writer.putf('<B', fmt.FORMAT_VERSION_4)
    header_writer.putf('<B', fmt.ModelType_v4.SKELETON_GEOMDEF_ST)
    header_writer.putf('<H', 0)  # shader id
    header_writer.putv3f(bbox[0])
    header_writer.putv3f(bbox[1])
    header_writer.putv3f(bsphere[0])
    header_writer.putf('<f', bsphere[1])
    chunked_writer.put(fmt.HEADER, header_writer)

    # search material
    used_materials = set()
    for face in bpy_obj.data.polygons:
        used_materials.add(face.material_index)
    for material_index in used_materials:
        material = bpy_obj.data.materials[material_index]
        if not material:
            raise log.AppError(
                text.error.obj_empty_mat,
                log.props(object=bpy_obj.name)
            )
    materials = set()
    for material_index, material in enumerate(bpy_obj.data.materials):
        if not material:
            continue
        if not material_index in used_materials:
            continue
        materials.add(material)
    materials = list(materials)
    if not len(materials):
        raise log.AppError(
            text.error.obj_no_mat,
            log.props(object=bpy_obj.name)
        )
    elif len(materials) > 1:
        raise log.AppError(
            text.error.many_mat,
            log.props(object=bpy_obj.name)
        )
    material = materials[0]
    two_sided = material.xray.flags_twosided

    # generate texture path
    texture_path = utils.material.get_image_relative_path(
        material,
        context,
        no_err=False
    )

    # write texture chunk
    texture_writer = rw.write.PackedWriter()
    texture_writer.puts(texture_path)
    texture_writer.puts(material.xray.eshader)
    chunked_writer.put(fmt.Chunks_v4.TEXTURE, texture_writer)

    # collect geometry data
    uv_layer = mesh.loops.layers.uv.active
    weight_layer = mesh.verts.layers.deform.verify()
    bpy_mesh.calc_tangents(uvmap=uv_layer.name)
    vertices = []
    triangles = []
    vertices_map = {}
    vertex_max_weights = 0
    for face in mesh.faces:
        face_indices = []
        for loop_index, loop in enumerate(face.loops):
            bpy_loop = bpy_mesh.loops[face.index * 3 + loop_index]
            uv = loop[uv_layer].uv

            # collect vertex weights
            weights = []
            weights_count = 0
            for group_index, weight in loop.vert[weight_layer].items():
                remap_group_index = vertex_groups_map.get(group_index, None)
                if not remap_group_index is None:
                    weights.append((remap_group_index, weight))
                    weights_count += 1
            if not weights_count:
                return log.AppError(
                    text.error.object_ungroupped_verts,
                    log.props(object=bpy_obj.name)
                )
            vertex_max_weights = max(vertex_max_weights, weights_count)

            bitan = bpy_loop.bitangent.normalized().to_tuple()
            vertex = (
                loop.vert.index,
                loop.vert.co.to_tuple(),
                bpy_loop.normal.to_tuple(),
                bpy_loop.tangent.to_tuple(),
                (-bitan[0], -bitan[1], -bitan[2]),
                (uv[0], 1 - uv[1]),
                tuple(weights)
            )
            vertex_index = vertices_map.get(vertex)
            if vertex_index is None:
                vertices_map[vertex] = vertex_index = len(vertices)
                vertices.append(vertex)
            face_indices.append(vertex_index)
        triangles.append(face_indices)
    utils.mesh.fix_ensure_lookup_table(mesh.verts)

    # write vertices chunk
    vertices_writer = rw.write.PackedWriter()
    vertices_count = len(vertices)
    if two_sided:
        vertices_count *= 2

    # 1-link vertices
    if vertex_max_weights == 1:
        if context.fmt_ver == 'soc':
            vert_fmt = fmt.VertexFormat.FVF_1L
        else:
            vert_fmt = fmt.VertexFormat.FVF_1L_CS

        vertices_writer.putf('<2I', vert_fmt, vertices_count)
        write_verts_1l(vertices_writer, vertices)

        if two_sided:
            write_verts_1l(vertices_writer, vertices, norm_coef=-1)

    # 2-link vertices
    else:
        if vertex_max_weights != 2:
            log.debug(
                'max_weights_count',
                count=vertex_max_weights
            )
        if context.fmt_ver == 'soc':
            vert_fmt = fmt.VertexFormat.FVF_2L
        else:
            vert_fmt = fmt.VertexFormat.FVF_2L_CS

        vertices_writer.putf('<2I', vert_fmt, vertices_count)
        write_verts_2l(vertices_writer, vertices)

        if two_sided:
            write_verts_2l(vertices_writer, vertices, norm_coef=-1)

    chunked_writer.put(fmt.Chunks_v4.VERTICES, vertices_writer)

    # write indices chunk
    indices_writer = rw.write.PackedWriter()

    indices_count = 3 * len(triangles)
    if two_sided:
        indices_count *= 2
    indices_writer.putf('<I', indices_count)

    for tris in triangles:
        indices_writer.putf('<3H', tris[0], tris[2], tris[1])

    if two_sided:
        offset = vertices_count // 2
        for tris in triangles:
            indices_writer.putf(
                '<3H',
                offset + tris[1],
                offset + tris[2],
                offset + tris[0]
            )

    chunked_writer.put(fmt.Chunks_v4.INDICES, indices_writer)


def vfunc(vtx_a, vtx_b, func):
    vtx_a.x = func(vtx_a.x, vtx_b.x)
    vtx_a.y = func(vtx_a.y, vtx_b.y)
    vtx_a.z = func(vtx_a.z, vtx_b.z)


def _write_header_bounds(obj, header_writer):
    # get bounds
    (b_min, b_max), (cntr, rad) = utils.mesh.calculate_bbox_and_bsphere(obj)

    # bbox
    header_writer.putv3f(b_min)    # min bbox
    header_writer.putv3f(b_max)    # max bbox

    # bsphere
    header_writer.putv3f(cntr)    # bsphere center
    header_writer.putf('<f', rad)    # bsphere radius


def _write_header_base(obj, header_writer):
    model_type = _get_model_type(obj.xray)
    header_writer.putf('<2BH', fmt.FORMAT_VERSION_4, model_type, FIRST_SHADER)


def _write_header(root_obj, ogf_writer):
    header_writer = rw.write.PackedWriter()

    _write_header_base(root_obj, header_writer)
    _write_header_bounds(root_obj, header_writer)

    ogf_writer.put(fmt.HEADER, header_writer)


def _get_model_type(xray):
    if len(xray.motionrefs_collection):
        model_type = fmt.ModelType_v4.SKELETON_ANIM

    elif len(xray.motions_collection) and context.export_motions:
        model_type = fmt.ModelType_v4.SKELETON_ANIM

    else:
        model_type = fmt.ModelType_v4.SKELETON_RIGID

    return model_type


def _write_revision(obj, ogf_writer):
    revision_writer = rw.write.PackedWriter()

    # get values
    owner, ctime, moder, mtime = utils.obj.get_revision_data(obj.xray.revision)
    build_time = int(time.time())

    # formatting build name
    prog_name = 'program: blender v{}.{}.{}'.format(*bpy.app.version)
    addon_name = 'addon: blender-xray-v{}.{}.{}'.format(*utils.addon_version)
    build_name = '{}, {}'.format(prog_name, addon_name)

    # formatting source file name
    blend_file = '*.blend file: "{}"'.format(bpy.data.filepath)
    obj_name = 'object: "{}"'.format(obj.name)
    source_file = '{}, {}'.format(blend_file, obj_name)

    # write
    revision_writer.puts(source_file)
    revision_writer.puts(build_name)
    revision_writer.putf('<I', build_time)
    revision_writer.puts(owner)
    revision_writer.putf('<I', ctime)
    revision_writer.puts(moder)
    revision_writer.putf('<I', mtime)

    # write chunk
    ogf_writer.put(fmt.Chunks_v4.S_DESC, revision_writer)


def _get_motion_context(context, arm_obj):
    motion_context = omf.ops.ExportOmfContext()

    motion_context.bpy_arm_obj = arm_obj
    motion_context.export_mode = 'OVERWRITE'
    motion_context.export_motions = True
    motion_context.export_bone_parts = True
    motion_context.need_motions = True
    motion_context.need_bone_groups = True

    if context.fmt_ver == 'soc':
        motion_context.params_ver = 3
        motion_context.high_quality = False
    else:
        motion_context.params_ver = 4
        motion_context.high_quality = context.hq_export

    return motion_context


def _write_motions(xray, context, arm_obj, ogf_writer):
    if context.export_motions and xray.motions_collection:
        motion_context = _get_motion_context(context, arm_obj)
        motions_writer = omf.exp.export_omf(motion_context)
        # append motions chunks
        ogf_writer.data.extend(motions_writer.data)


def _write_motion_refs(obj, context, ogf_writer):
    refs_collect = obj.xray.motionrefs_collection

    if len(refs_collect):
        refs_writer = rw.write.PackedWriter()
        refs = [ref.name for ref in refs_collect]

        # soc format
        if context.fmt_ver == 'soc':
            refs_string = ','.join(refs)
            refs_writer.puts(refs_string)
            chunk_id = fmt.Chunks_v4.S_MOTION_REFS_0

        # cs/cop format
        else:
            refs_count = len(refs)
            refs_writer.putf('<I', refs_count)
            for ref in refs:
                refs_writer.puts(ref)
            chunk_id = fmt.Chunks_v4.S_MOTION_REFS_2

        ogf_writer.put(chunk_id, refs_writer)


def _write_userdata(obj, ogf_writer):
    userdata = obj.xray.userdata

    if userdata:
        userdata_writer = rw.write.PackedWriter()
        userdata_writer.puts(userdata)
        ogf_writer.put(fmt.Chunks_v4.S_USERDATA, userdata_writer)


def _write_ik_data(bones, scale, ogf_writer):
    ik_writer = rw.write.PackedWriter()
    mul = utils.version.get_multiply()

    for bone, obj in bones:
        xray = bone.xray

        # get types
        shape_type = utils.bone.get_bone_prop(xray.shape, 'type', 4)
        ik_type = utils.bone.get_bone_prop(xray.ikjoint, 'type', 6)

        # get shapes

        # box translation and half size
        box_trn = mathutils.Vector(xray.shape.box_trn) * scale
        box_hsz = mathutils.Vector(xray.shape.box_hsz) * scale

        # sphere position and radius
        sph_pos = mathutils.Vector(xray.shape.sph_pos) * scale
        sph_rad = xray.shape.sph_rad * scale

        # cylinder position, height, radius
        cyl_pos = mathutils.Vector(xray.shape.cyl_pos) * scale
        cyl_hgt = xray.shape.cyl_hgh * scale
        cyl_rad = xray.shape.cyl_rad * scale

        # get limits
        x_min, x_max = utils.bone.get_ode_ik_limits(
            xray.ikjoint.lim_x_min,
            xray.ikjoint.lim_x_max
        )
        y_min, y_max = utils.bone.get_ode_ik_limits(
            xray.ikjoint.lim_y_min,
            xray.ikjoint.lim_y_max
        )
        z_min, z_max = utils.bone.get_ode_ik_limits(
            xray.ikjoint.lim_z_min,
            xray.ikjoint.lim_z_max
        )

        # get center of mass
        cmass = mathutils.Vector(xray.mass.center) * scale

        # get bind pose matrix

        # bind pose matrix
        mat = mul(bone.matrix_local, motions.const.MATRIX_BONE_INVERTED)
        # parent bone
        par = utils.bone.find_bone_exportable_parent(bone)

        if par:
            # parent matrix
            pmat = mul(par.matrix_local, motions.const.MATRIX_BONE_INVERTED)
            # bind pose matrix
            mat = mul(pmat.inverted(), mat)

        # bind rotation
        euler = mat.to_euler('YXZ')
        euler.x = -euler.x
        euler.y = -euler.y
        euler.z = -euler.z

        # bind translation
        trn = mat.to_translation() * scale

        # write

        # header
        ik_writer.putf('<I', fmt.BONE_VERSION_1)
        ik_writer.puts(xray.gamemtl)
        ik_writer.putf('<2H', shape_type, xray.shape.flags)

        # shapes
        ik_writer.putf(
            '<27f',

            # box
            *xray.shape.box_rot,    # box rotate 3x3 matrix 9 float
            *box_trn,    # box translate 3 float
            *box_hsz,    # box half size 3 float

            # sphere
            *sph_pos,    # sphere position 3 float
            sph_rad,    # sphere radius 1 float

            # cylinder
            *cyl_pos,    # cylinder position 3 float
            *xray.shape.cyl_dir,    # cylinder direction 3 float
            cyl_hgt,    # cylinder height 1 float
            cyl_rad    # cylinder radius 1 float
        )

        # limits and others
        ik_writer.putf(
            '<I14fI3f',

            ik_type,

            # x limits
            x_min,
            x_max,
            xray.ikjoint.lim_x_spr,
            xray.ikjoint.lim_x_dmp,

            # y limits
            y_min,
            y_max,
            xray.ikjoint.lim_y_spr,
            xray.ikjoint.lim_y_dmp,

            # z limits
            z_min,
            z_max,
            xray.ikjoint.lim_z_spr,
            xray.ikjoint.lim_z_dmp,

            xray.ikjoint.spring,
            xray.ikjoint.damping,

            xray.ikflags,

            xray.breakf.force,
            xray.breakf.torque,
            xray.friction
        )

        # bind pose
        ik_writer.putv3f(euler)
        ik_writer.putv3f(trn)

        # mass
        ik_writer.putf('<f', xray.mass.value)
        ik_writer.putv3f(cmass)

    # write chunk
    ogf_writer.put(fmt.Chunks_v4.S_IKDATA_2, ik_writer)


def _export_main(root_obj, ogf_writer, context):
    xray = root_obj.xray

    # header
    _write_header(root_obj, ogf_writer)

    # revision
    _write_revision(root_obj, ogf_writer)

    meshes = []
    armatures = []
    bones = []
    bones_map = {}

    def reg_bone(bone, adv):
        idx = bones_map.get(bone, -1)
        if idx == -1:
            idx = len(bones)
            bones.append((bone, adv))
            bones_map[bone] = idx
        return idx

    def scan_r(bpy_obj):
        if utils.obj.is_helper_object(bpy_obj):
            return
        if bpy_obj.type == 'MESH':
            arm_obj = utils.obj.get_armature_object(bpy_obj)
            if not arm_obj:
                raise log.AppError(
                    text.error.ogf_has_no_arm,
                    log.props(object=bpy_obj.name)
                )

            # check uv-maps
            uv_layers = bpy_obj.data.uv_layers
            if not len(uv_layers):
                raise log.AppError(
                    text.error.no_uv,
                    log.props(object=bpy_obj.name)
                )
            elif len(uv_layers) > 1:
                log.warn(
                    text.warn.obj_many_uv,
                    exported_uv=uv_layers.active.name,
                    mesh_object=bpy_obj.name
                )

            vertex_groups_map = {}
            for group_index, group in enumerate(bpy_obj.vertex_groups):
                bone = arm_obj.data.bones.get(group.name, None)
                if bone is None:
                    continue
                vertex_groups_map[group_index] = reg_bone(bone, arm_obj)
            child_objects = []
            remove_child_objects = False
            if len(bpy_obj.material_slots) > 1:
                # separate by materials
                bpy.ops.object.select_all(action='DESELECT')
                multi_material_mesh = bpy_obj.data.copy()
                multi_material_object = bpy_obj.copy()
                multi_material_object.data = multi_material_mesh
                utils.version.link_object(multi_material_object)
                utils.version.set_active_object(multi_material_object)
                temp_parent_object = bpy.data.objects.new('!-temp-parent-object', None)
                utils.version.link_object(temp_parent_object)
                multi_material_object.parent = temp_parent_object
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.separate(type='MATERIAL')
                bpy.ops.object.mode_set(mode='OBJECT')
                for child_object in temp_parent_object.children:
                    child_objects.append(child_object)
                bpy.data.objects.remove(temp_parent_object)
                remove_child_objects = True
            else:
                child_objects.append(bpy_obj)
            for child_object in child_objects:
                mesh_writer = rw.write.ChunkedWriter()
                error = _export_child(
                    root_obj,
                    child_object,
                    mesh_writer,
                    context,
                    vertex_groups_map
                )
                meshes.append(mesh_writer)
                if remove_child_objects:
                    child_mesh = child_object.data
                    bpy.data.objects.remove(child_object)
                    bpy.data.meshes.remove(child_mesh)
                if error:
                    raise error
        elif bpy_obj.type == 'ARMATURE':
            armatures.append(bpy_obj)
            for bone in bpy_obj.data.bones:
                if not utils.bone.is_exportable_bone(bone):
                    continue
                reg_bone(bone, bpy_obj)
        for child in bpy_obj.children:
            scan_r(child)

    scan_r(root_obj)

    if len(armatures) > 1:
        raise log.AppError(
            text.error.object_many_arms,
            log.props(
                root_object=root_obj.name,
                armatures=[arm.name for arm in armatures]
            )
        )

    arm_obj = armatures[0]

    # export children
    child_index = 0
    children_writer = rw.write.ChunkedWriter()

    for mesh_writer in meshes:
        children_writer.put(child_index, mesh_writer)
        child_index += 1

    ogf_writer.put(fmt.Chunks_v4.CHILDREN, children_writer)

    # get armature scale
    _, scale_vec = utils.ie.get_obj_scale_matrix(root_obj, arm_obj)
    scale = utils.ie.check_armature_scale(scale_vec, root_obj, arm_obj)
    multiply = utils.version.get_multiply()

    # export bone names
    bones_writer = rw.write.PackedWriter()
    bones_writer.putf('<I', len(bones))

    for bone, _ in bones:
        b_parent = utils.bone.find_bone_exportable_parent(bone)

        # names
        bones_writer.puts(bone.name)
        if b_parent:
            parent_name = b_parent.name
        else:
            parent_name = ''
        bones_writer.puts(parent_name)

        bxray = bone.xray

        # generate obb
        verts = utils.bone.bone_vertices(bone)

        if len(verts) > 3:
            bone_mat = utils.bone.get_obb(bone, False)

            # generate aabb
            if not bone_mat:
                vmin = mathutils.Vector((+math.inf, +math.inf, +math.inf))
                vmax = mathutils.Vector((-math.inf, -math.inf, -math.inf))

                for vtx in verts:
                    vfunc(vmin, vtx, min)
                    vfunc(vmax, vtx, max)

                if vmax.x > vmin.x:
                    vcenter = (vmax + vmin) / 2
                    vscale = (vmax - vmin) / 2
                    bone_mat = multiply(
                        mathutils.Matrix.Identity(4),
                        mathutils.Matrix.Translation(vcenter),
                        utils.bone.convert_vector_to_matrix(vscale)
                    )

            if bone_mat:
                bone_mat = multiply(
                    multiply(
                        bone.matrix_local,
                        mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
                    ).inverted(),
                    bone_mat
                )

                bone_mat = multiply(
                    bone_mat,
                    mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
                )
                box_trn = list(bone_mat.to_translation().to_tuple())

                bone_scale = bone_mat.to_scale()
                for axis in range(3):
                    if not bone_scale[axis]:
                        bone_scale[axis] = 0.0001

                box_hsz = list(bone_scale.to_tuple())

                mat_rot = multiply(
                    bone_mat,
                    utils.bone.convert_vector_to_matrix(bone_scale).inverted()
                ).to_3x3().transposed()

                box_rot = []
                for row in range(3):
                    box_rot.extend(mat_rot[row].to_tuple())

                box_trn[0] *= scale
                box_trn[1] *= scale
                box_trn[2] *= scale

                box_hsz[0] *= scale
                box_hsz[1] *= scale
                box_hsz[2] *= scale

            else:
                box_rot = (
                    1.0, 0.0, 0.0,
                    0.0, 1.0, 0.0,
                    0.0, 0.0, 1.0
                )
                box_trn = (0.0, 0.0, 0.0)
                box_hsz = (0.0, 0.0, 0.0)

        else:
            box_rot = (
                1.0, 0.0, 0.0,
                0.0, 1.0, 0.0,
                0.0, 0.0, 1.0
            )
            box_trn = (0.0, 0.0, 0.0)
            box_hsz = (0.0, 0.0, 0.0)

        # bone rotation
        bones_writer.putf('<9f', *box_rot)

        # bone translation
        bones_writer.putf('<3f', *box_trn)

        # bone half size
        bones_writer.putf('<3f', *box_hsz)

    ogf_writer.put(fmt.Chunks_v4.S_BONE_NAMES, bones_writer)

    _write_ik_data(bones, scale, ogf_writer)
    _write_userdata(root_obj, ogf_writer)
    _write_motion_refs(root_obj, context, ogf_writer)
    _write_motions(xray, context, arm_obj, ogf_writer)


@log.with_context('export-object')
@utils.stats.timer
def export_file(bpy_obj, file_path, context):
    utils.stats.status('Export File', file_path)
    log.update(object=bpy_obj.name)

    ogf_writer = rw.write.ChunkedWriter()
    _export_main(bpy_obj, ogf_writer, context)
    rw.utils.save_file(file_path, ogf_writer)
