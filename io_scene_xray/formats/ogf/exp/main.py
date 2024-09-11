# standart modules
import time

# blender modules
import bpy
import bmesh
import mathutils

# addon modules
from .. import fmt
from ... import omf
from ... import motions
from .... import text
from .... import inspect
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
            weights = utils.mesh.weights_top(weights, 2)
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


def write_verts_3l(vertices_writer, vertices, norm_coef=1):
    for vertex in vertices:
        weights = vertex[6]

        # 3-link vertex
        if len(weights) == 3:
            group_1 = weights[0][0]
            group_2 = weights[1][0]
            group_3 = weights[2][0]

            weight_1 = weights[0][1]
            weight_2 = weights[1][1]
            weight_3 = weights[2][1]

            weight_sum = weight_1 + weight_2 + weight_3

            # normalize
            weight_1_norm = weight_1 / weight_sum
            weight_2_norm = weight_2 / weight_sum

            vertices_writer.putf('<3H', group_1, group_2, group_3)

        # 2-link vertex
        elif len(weights) == 2:
            group_1 = weights[0][0]
            group_2 = weights[1][0]

            weight_1 = weights[0][1]
            weight_2 = weights[1][1]

            weight_sum = weight_1 + weight_2

            # normalize
            weight_1_norm = weight_1 / weight_sum
            weight_2_norm = weight_2 / weight_sum

            vertices_writer.putf('<3H', group_1, group_2, group_1)

        # 1-link vertex
        elif len(weights) == 1:
            group_1 = weights[0][0]

            weight_1_norm = 1.0
            weight_2_norm = 0.0

            vertices_writer.putf('<3H', group_1, group_1, group_1)

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
        vertices_writer.putf('<2f', weight_1_norm, weight_2_norm)    # weights
        vertices_writer.putf('<2f', *vertex[5])    # uv


def write_verts_4l(vertices_writer, vertices, norm_coef=1):
    for vertex in vertices:
        weights = vertex[6]

        if len(weights) > 4:
            weights = utils.mesh.weights_top(weights, 4)

        # 4-link vertex
        if len(weights) == 4:
            group_1 = weights[0][0]
            group_2 = weights[1][0]
            group_3 = weights[2][0]
            group_4 = weights[3][0]

            weight_1 = weights[0][1]
            weight_2 = weights[1][1]
            weight_3 = weights[2][1]
            weight_4 = weights[3][1]

            weight_sum = weight_1 + weight_2 + weight_3 + weight_4

            # normalize
            weight_1_norm = weight_1 / weight_sum
            weight_2_norm = weight_2 / weight_sum
            weight_3_norm = weight_3 / weight_sum

            vertices_writer.putf('<4H', group_1, group_2, group_3, group_4)

        # 3-link vertex
        elif len(weights) == 3:
            group_1 = weights[0][0]
            group_2 = weights[1][0]
            group_3 = weights[2][0]

            weight_1 = weights[0][1]
            weight_2 = weights[1][1]
            weight_3 = weights[2][1]

            weight_sum = weight_1 + weight_2 + weight_3

            # normalize
            weight_1_norm = weight_1 / weight_sum
            weight_2_norm = weight_2 / weight_sum
            weight_3_norm = weight_3 / weight_sum

            vertices_writer.putf('<4H', group_1, group_2, group_3, group_1)

        # 2-link vertex
        elif len(weights) == 2:
            group_1 = weights[0][0]
            group_2 = weights[1][0]

            weight_1 = weights[0][1]
            weight_2 = weights[1][1]

            weight_sum = weight_1 + weight_2

            # normalize
            weight_1_norm = weight_1 / weight_sum
            weight_2_norm = weight_2 / weight_sum
            weight_3_norm = 0.0

            vertices_writer.putf('<4H', group_1, group_2, group_1, group_1)

        # 1-link vertex
        elif len(weights) == 1:
            group_1 = weights[0][0]

            weight_1_norm = 1.0
            weight_2_norm = 0.0
            weight_3_norm = 0.0

            vertices_writer.putf('<4H', group_1, group_1, group_1, group_1)

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
        # weights
        vertices_writer.putf(
            '<3f',
            weight_1_norm,
            weight_2_norm,
            weight_3_norm
        )
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
    header_writer.putf('<H', 0)    # shader id
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
                if remap_group_index is not None:
                    weights.append((remap_group_index, weight))
                    weights_count += 1

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

    if vertices_count > fmt.VERTS_COUNT_LIMIT:
        raise log.AppError(
            text.error.ogf_verts_count_limit,
            log.props(
                vertices_count=vertices_count,
                vertices_count_limit=fmt.VERTS_COUNT_LIMIT,
                object=bpy_obj.name
            )
        )

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
    elif vertex_max_weights == 2 or context.fmt_ver == 'soc':
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

    # 3-link vertices
    elif vertex_max_weights == 3:
        vert_fmt = fmt.VertexFormat.FVF_3L_CS

        vertices_writer.putf('<2I', vert_fmt, vertices_count)
        write_verts_3l(vertices_writer, vertices)

        if two_sided:
            write_verts_3l(vertices_writer, vertices, norm_coef=-1)

    # 4-link vertices
    else:
        vert_fmt = fmt.VertexFormat.FVF_4L_CS

        vertices_writer.putf('<2I', vert_fmt, vertices_count)
        write_verts_4l(vertices_writer, vertices)

        if two_sided:
            write_verts_4l(vertices_writer, vertices, norm_coef=-1)

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

    # remove temp mesh
    bpy.data.meshes.remove(bpy_mesh)

    chunked_writer.put(fmt.Chunks_v4.INDICES, indices_writer)


def _write_header_bounds(obj, header_writer):
    # get bounds
    (b_min, b_max), (cntr, rad) = utils.mesh.calculate_bbox_and_bsphere(obj)

    # bbox
    header_writer.putv3f(b_min)    # min bbox
    header_writer.putv3f(b_max)    # max bbox

    # bsphere
    header_writer.putv3f(cntr)    # bsphere center
    header_writer.putf('<f', rad)    # bsphere radius


def _write_header_base(obj, header_writer, context):
    model_type = _get_model_type(obj.xray, context)
    header_writer.putf('<2BH', fmt.FORMAT_VERSION_4, model_type, FIRST_SHADER)


def _write_header(root_obj, ogf_writer, context):
    header_writer = rw.write.PackedWriter()

    _write_header_base(root_obj, header_writer, context)
    _write_header_bounds(root_obj, header_writer)

    ogf_writer.put(fmt.HEADER, header_writer)


def _get_model_type(xray, context):
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
    owner, ctime, moder, mtime = utils.obj.get_revis(obj.xray.revision)
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


def _write_lod(root_obj, ogf_writer):
    lod = root_obj.xray.lodref

    if lod:
        lod_writer = rw.write.PackedWriter()
        lod_writer.puts(lod + '\r\n')
        ogf_writer.put(fmt.Chunks_v4.S_LODS, lod_writer)


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
        x_min, x_max = utils.bone.get_x_limits(xray.ikjoint)
        x_min, x_max = utils.bone.get_ode_ik_limits(x_min, x_max)
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


def _write_children(meshes, ogf_writer):
    children_writer = rw.write.ChunkedWriter()

    for child_index, mesh_writer in enumerate(meshes):
        children_writer.put(child_index, mesh_writer)

    ogf_writer.put(fmt.Chunks_v4.CHILDREN, children_writer)


def _get_default_bone_bound():
    box_rot = (
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
        0.0, 0.0, 1.0
    )
    box_trn = (0.0, 0.0, 0.0)
    box_hsz = (0.0, 0.0, 0.0)
    return box_rot, box_trn, box_hsz


MATRIX_BONE = mathutils.Matrix.Scale(-1, 4, (0, 0, 1)).freeze()


def _bone_mat_to_scale(bone_mat):
    bone_scale = bone_mat.to_scale()

    for axis in range(3):
        if not bone_scale[axis]:
            bone_scale[axis] = 0.0001

    return bone_scale


def _bone_mat_to_rotate(bone_mat, bone_scale, mul):
    scale_mat = utils.bone.convert_vector_to_matrix(bone_scale)
    mat_rot = mul(bone_mat, scale_mat.inverted()).to_3x3().transposed()

    box_rot = []
    for row in range(3):
        box_rot.extend(mat_rot[row].to_tuple())

    return box_rot


def _get_bone_half_size(bone_scale, scale):
    half_size = bone_scale * scale

    for axis in range(3):
        half_size[axis] = abs(half_size[axis])

    return half_size


def _get_bone_box(bone, bone_mat, scale, mul):
    local_mat = mul(bone.matrix_local, MATRIX_BONE)
    bone_mat = mul(local_mat.inverted(), bone_mat)
    bone_mat = mul(bone_mat, MATRIX_BONE)
    bone_scale = _bone_mat_to_scale(bone_mat)

    box_rot = _bone_mat_to_rotate(bone_mat, bone_scale, mul)
    box_trn = bone_mat.to_translation() * scale
    box_hsz = _get_bone_half_size(bone_scale, scale)

    return box_rot, box_trn, box_hsz


def _get_bone_bound(bone, scale, mul):
    verts, _ = utils.bone.bone_vertices(bone)

    if len(verts) > 3:
        # generate obb
        mat = utils.bone.get_obb(bone, False, 0.0)

        if not mat:
            # generate aabb
            mat = utils.bone.get_aabb(verts)

        if mat:
            box_rot, box_trn, box_hsz = _get_bone_box(bone, mat, scale, mul)

        else:
            box_rot, box_trn, box_hsz = _get_default_bone_bound()

    else:
        box_rot, box_trn, box_hsz = _get_default_bone_bound()

    return box_rot, box_trn, box_hsz


def _write_bone_names(bones, scale, ogf_writer):
    bones_writer = rw.write.PackedWriter()

    bones_count = len(bones)
    bones_writer.putf('<I', bones_count)

    multiply = utils.version.get_multiply()

    for bone, _ in bones:
        parent = utils.bone.find_bone_exportable_parent(bone)

        if parent:
            parent_name = parent.name
        else:
            parent_name = ''

        # bone bound
        box_rot, box_trn, box_hsz = _get_bone_bound(bone, scale, multiply)

        # write
        bones_writer.puts(bone.name)
        bones_writer.puts(parent_name)
        bones_writer.putf('<15f', *box_rot, *box_trn, *box_hsz)

    # write chunk
    ogf_writer.put(fmt.Chunks_v4.S_BONE_NAMES, bones_writer)


def reg_bone(bones, bones_map, bone, adv):
    bone_index = bones_map.get(bone, None)

    if bone_index is None:
        bone_index = len(bones)
        bones.append((bone, adv))
        bones_map[bone] = bone_index

    return bone_index


def scan_root(bpy_obj, root_obj, meshes, arms, bones, bones_map, context):
    if utils.obj.is_helper_object(bpy_obj):
        return

    # scan mesh
    if bpy_obj.type == 'MESH':
        arm_obj = utils.obj.get_armature_object(bpy_obj)
        if not arm_obj:
            raise log.AppError(
                text.error.ogf_has_no_arm,
                log.props(object=bpy_obj.name)
            )

        # check vertex weights
        utils.ie.validate_vertex_weights(bpy_obj, arm_obj)

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

        # collect vertex groups
        vertex_groups_map = {}

        for group_index, group in enumerate(bpy_obj.vertex_groups):
            bone = arm_obj.data.bones.get(group.name, None)

            if bone is None:
                continue

            if not utils.bone.is_exportable_bone(bone):
                continue

            vertex_groups_map[group_index] = reg_bone(
                bones,
                bones_map,
                bone,
                arm_obj
            )

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
            _export_child(
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

    # scan armature
    elif bpy_obj.type == 'ARMATURE':
        arms.append(bpy_obj)
        for bone in bpy_obj.data.bones:
            if not utils.bone.is_exportable_bone(bone):
                continue
            reg_bone(bones, bones_map, bone, bpy_obj)


def _get_arm_scale(root_obj, arm_obj):
    _, scale_vec = utils.ie.get_obj_scale_matrix(root_obj, arm_obj)
    scale = utils.ie.check_armature_scale(scale_vec, root_obj, arm_obj)
    return scale


def _get_arm(root_obj, arms):
    if len(arms) > 1:
        raise log.AppError(
            text.error.object_many_arms,
            log.props(
                root_object=root_obj.name,
                armatures=[arm.name for arm in arms]
            )
        )

    arm_obj = arms[0]
    return arm_obj


def _export_main(root_obj, ogf_writer, context):
    xray = root_obj.xray

    meshes = []
    arms = []
    bones = []
    bones_map = {}

    exp_objs = utils.obj.get_exp_objs(context, root_obj)
    for obj in exp_objs:
        scan_root(obj, root_obj, meshes, arms, bones, bones_map, context)

    # get armature
    arm_obj = _get_arm(root_obj, arms)

    # check bone names
    inspect.bone.check_bone_names(arm_obj)

    # get armature scale
    scale = _get_arm_scale(root_obj, arm_obj)

    # write
    _write_header(root_obj, ogf_writer, context)
    _write_revision(root_obj, ogf_writer)
    _write_children(meshes, ogf_writer)
    _write_bone_names(bones, scale, ogf_writer)
    _write_ik_data(bones, scale, ogf_writer)
    _write_userdata(root_obj, ogf_writer)
    _write_motion_refs(root_obj, context, ogf_writer)
    _write_motions(xray, context, arm_obj, ogf_writer)
    _write_lod(root_obj, ogf_writer)


@log.with_context('export-ogf')
@utils.stats.timer
def export_file(bpy_obj, file_path, context):
    utils.stats.status('Export File', file_path)
    log.update(object=bpy_obj.name)

    ogf_writer = rw.write.ChunkedWriter()
    _export_main(bpy_obj, ogf_writer, context)
    rw.utils.save_file(file_path, ogf_writer)
