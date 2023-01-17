# standart modules
import math
import time

# blender modules
import bpy
import bmesh
import mathutils

# addon modules
from . import fmt
from .. import omf
from .. import motions
from ... import text
from ... import rw
from ... import log
from ... import utils


multiply = utils.version.get_multiply()


def calculate_mesh_bsphere(bbox, vertices, mat=mathutils.Matrix()):
    center = (bbox[0] + bbox[1]) / 2
    _delta = bbox[1] - bbox[0]
    max_radius = max(abs(_delta.x), abs(_delta.y), abs(_delta.z)) / 2
    for vtx in vertices:
        relative = multiply(mat, vtx.co) - center
        radius = relative.length
        if radius > max_radius:
            offset = center - relative.normalized() * max_radius
            center = (multiply(mat, vtx.co) + offset) / 2
            max_radius = (center - offset).length
    return center, max_radius


def calculate_bbox_and_bsphere(bpy_obj, apply_transforms=False, cache=None):
    def scan_meshes(bpy_obj, meshes):
        if utils.is_helper_object(bpy_obj):
            return
        if (bpy_obj.type == 'MESH') and bpy_obj.data.vertices:
            meshes.append(bpy_obj)
        for child in bpy_obj.children:
            scan_meshes(child, meshes)

    def scan_meshes_using_cache(bpy_obj, meshes, cache):
        if utils.is_helper_object(bpy_obj):
            return
        if (bpy_obj.type == 'MESH') and bpy_obj.data.vertices:
            meshes.append(bpy_obj)
        for child_name in cache.children[bpy_obj.name]:
            child = bpy.data.objects[child_name]
            scan_meshes_using_cache(child, meshes, cache)

    meshes = []
    if cache:
        scan_meshes_using_cache(bpy_obj, meshes, cache)
    else:
        scan_meshes(bpy_obj, meshes)

    bbox = None
    spheres = []
    for bpy_mesh in meshes:
        if cache:
            if cache.bounds.get(bpy_mesh.name, None):
                bbx, center, radius = cache.bounds[bpy_mesh.name]
            else:
                if apply_transforms:
                    mat_world = bpy_mesh.matrix_world
                else:
                    mat_world = mathutils.Matrix()
                mesh = utils.mesh.convert_object_to_space_bmesh(bpy_mesh, mat_world)
                bbx = utils.mesh.calculate_mesh_bbox(mesh.verts, mat=mat_world)
                center, radius = calculate_mesh_bsphere(bbx, mesh.verts, mat=mat_world)
                cache.bounds[bpy_mesh.name] = bbx, center, radius
        else:
            if apply_transforms:
                mat_world = bpy_mesh.matrix_world
            else:
                mat_world = mathutils.Matrix()
            mesh = utils.mesh.convert_object_to_space_bmesh(bpy_mesh, mat_world)
            bbx = utils.mesh.calculate_mesh_bbox(mesh.verts, mat=mat_world)
            center, radius = calculate_mesh_bsphere(bbx, mesh.verts, mat=mat_world)

        if bbox is None:
            bbox = bbx
        else:
            for axis in range(3):
                bbox[0][axis] = min(bbox[0][axis], bbx[0][axis])
                bbox[1][axis] = max(bbox[1][axis], bbx[1][axis])
        spheres.append((center, radius))

    center = mathutils.Vector()
    radius = 0
    if not spheres:
        return (mathutils.Vector(), mathutils.Vector()), (center, radius)
    for sphere in spheres:
        center += sphere[0]
    center /= len(spheres)
    for ctr, rad in spheres:
        radius = max(radius, (ctr - center).length + rad)
    return bbox, (center, radius)


def top_two(dic):
    def top_one(dic, skip=None):
        max_key = None
        max_val = -1
        for key, val in dic:
            if (key != skip) and (val > max_val):
                max_val = val
                max_key = key
        return max_key, max_val

    key0, val0 = top_one(dic)
    key1, val1 = top_one(dic, key0)
    return [(key0, val0), (key1, val1)]


def _export_child(bpy_obj, chunked_writer, context, vertex_groups_map):
    # validate mesh-object
    uv_layers = bpy_obj.data.uv_layers
    if not len(uv_layers):
        raise log.AppError(
            text.error.no_uv,
            log.props(object=bpy_obj.name)
        )
    elif len(uv_layers) > 1:
        raise log.AppError(
            text.error.obj_many_uv,
            log.props(object=bpy_obj.name)
        )

    mesh = utils.mesh.convert_object_to_space_bmesh(
        bpy_obj,
        mathutils.Matrix.Identity(4)
    )
    bbox = utils.mesh.calculate_mesh_bbox(mesh.verts)
    bsphere = calculate_mesh_bsphere(bbox, mesh.verts)
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
    # 1-link vertices
    if vertex_max_weights == 1:
        vertices_writer.putf('<2I', fmt.VertexFormat.FVF_1L, vertices_count)
        for vertex in vertices:
            vertices_writer.putv3f(vertex[1])    # coord
            vertices_writer.putv3f(vertex[2])    # normal
            vertices_writer.putv3f(vertex[3])    # tangent
            vertices_writer.putv3f(vertex[4])    # bitangent
            vertices_writer.putf('<2f', *vertex[5])    # uv
            vertices_writer.putf('<I', vertex[6][0][0])
    # 2-link vertices
    else:
        if vertex_max_weights != 2:
            log.debug(
                'max_weights_count',
                count=vertex_max_weights
            )
        vertices_writer.putf('<2I', fmt.VertexFormat.FVF_2L, vertices_count)
        for vertex in vertices:
            weights = vertex[6]
            if len(weights) > 2:
                weights = top_two(weights)
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
                raise Exception('oops: %i %s' % (len(weights), weights.keys()))
            # write vertex data
            vertices_writer.putv3f(vertex[1])    # coord
            vertices_writer.putv3f(vertex[2])    # normal
            vertices_writer.putv3f(vertex[3])    # tangent
            vertices_writer.putv3f(vertex[4])    # bitangent
            vertices_writer.putf('<f', weight)    # weight
            vertices_writer.putf('<2f', *vertex[5])    # uv
    chunked_writer.put(fmt.Chunks_v4.VERTICES, vertices_writer)

    # write indices chunk
    indices_writer = rw.write.PackedWriter()
    indices_writer.putf('<I', 3 * len(triangles))
    for tris in triangles:
        indices_writer.putf('<3H', tris[0], tris[2], tris[1])
    chunked_writer.put(fmt.Chunks_v4.INDICES, indices_writer)


def get_ode_ik_limits(value_1, value_2):
    # swap special for ODE
    min_value = min(-value_1, -value_2)
    max_value = max(-value_1, -value_2)
    return min_value, max_value


def _export(bpy_obj, cwriter, context):
    bbox, bsph = calculate_bbox_and_bsphere(bpy_obj)
    xray = bpy_obj.xray
    if len(xray.motionrefs_collection):
        model_type = fmt.ModelType_v4.SKELETON_ANIM
    elif len(xray.motions_collection) and context.export_motions:
        model_type = fmt.ModelType_v4.SKELETON_ANIM
    else:
        model_type = fmt.ModelType_v4.SKELETON_RIGID

    header_writer = rw.write.PackedWriter()
    header_writer.putf('<B', fmt.FORMAT_VERSION_4)  # ogf version
    header_writer.putf('<B', model_type)
    header_writer.putf('<H', 0)  # shader id
    # bbox
    header_writer.putv3f(bbox[0])
    header_writer.putv3f(bbox[1])
    # bsphere
    header_writer.putv3f(bsph[0])
    header_writer.putf('<f', bsph[1])
    cwriter.put(fmt.HEADER, header_writer)

    owner, ctime, moder, mtime = utils.get_revision_data(xray.revision)
    currtime = int(time.time())
    revision_writer = rw.write.PackedWriter()
    revision_writer.puts(bpy_obj.name)    # source file
    revision_writer.puts('blender')    # build name
    revision_writer.putf('<I', currtime)    # build time
    revision_writer.puts(owner)
    revision_writer.putf('<I', ctime)
    revision_writer.puts(moder)
    revision_writer.putf('<I', mtime)
    cwriter.put(fmt.Chunks_v4.S_DESC, revision_writer)

    meshes = []
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
        if utils.is_helper_object(bpy_obj):
            return
        if bpy_obj.type == 'MESH':
            arm_obj = utils.get_armature_object(bpy_obj)
            if not arm_obj:
                raise log.AppError(
                    text.error.ogf_has_no_arm,
                    log.props(object=bpy_obj.name)
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
            for bone in bpy_obj.data.bones:
                if not utils.bone.is_exportable_bone(bone):
                    continue
                reg_bone(bone, bpy_obj)
        for child in bpy_obj.children:
            scan_r(child)

    scan_r(bpy_obj)

    children_chunked_writer = rw.write.ChunkedWriter()
    mesh_index = 0
    for mesh_writer in meshes:
        children_chunked_writer.put(mesh_index, mesh_writer)
        mesh_index += 1
    cwriter.put(fmt.Chunks_v4.CHILDREN, children_chunked_writer)

    pwriter = rw.write.PackedWriter()
    pwriter.putf('<I', len(bones))
    for bone, _ in bones:
        b_parent = utils.bone.find_bone_exportable_parent(bone)
        pwriter.puts(bone.name)
        pwriter.puts(b_parent.name if b_parent else '')
        xray = bone.xray
        pwriter.putf('<9f', *xray.shape.box_rot)
        pwriter.putf('<3f', *xray.shape.box_trn)
        pwriter.putf('<3f', *xray.shape.box_hsz)
    cwriter.put(fmt.Chunks_v4.S_BONE_NAMES, pwriter)

    pwriter = rw.write.PackedWriter()
    for bone, obj in bones:
        xray = bone.xray
        pwriter.putf('<I', 0x1)  # version
        pwriter.puts(xray.gamemtl)
        pwriter.putf('<H', int(xray.shape.type))
        pwriter.putf('<H', xray.shape.flags)
        pwriter.putf('<9f', *xray.shape.box_rot)
        pwriter.putf('<3f', *xray.shape.box_trn)
        pwriter.putf('<3f', *xray.shape.box_hsz)
        pwriter.putf('<3f', *xray.shape.sph_pos)
        pwriter.putf('<f', xray.shape.sph_rad)
        pwriter.putf('<3f', *xray.shape.cyl_pos)
        pwriter.putf('<3f', *xray.shape.cyl_dir)
        pwriter.putf('<f', xray.shape.cyl_hgh)
        pwriter.putf('<f', xray.shape.cyl_rad)
        pwriter.putf('<I', int(xray.ikjoint.type))

        # x axis
        x_min, x_max = get_ode_ik_limits(
            xray.ikjoint.lim_x_min,
            xray.ikjoint.lim_x_max
        )
        pwriter.putf('<2f', x_min, x_max)
        pwriter.putf('<2f', xray.ikjoint.lim_x_spr, xray.ikjoint.lim_x_dmp)

        # y axis
        y_min, y_max = get_ode_ik_limits(
            xray.ikjoint.lim_y_min,
            xray.ikjoint.lim_y_max
        )
        pwriter.putf('<2f', y_min, y_max)
        pwriter.putf('<2f', xray.ikjoint.lim_y_spr, xray.ikjoint.lim_y_dmp)

        # z axis
        z_min, z_max = get_ode_ik_limits(
            xray.ikjoint.lim_z_min,
            xray.ikjoint.lim_z_max
        )
        pwriter.putf('<2f', z_min, z_max)
        pwriter.putf('<2f', xray.ikjoint.lim_z_spr, xray.ikjoint.lim_z_dmp)

        pwriter.putf('<2f', xray.ikjoint.spring, xray.ikjoint.damping)
        pwriter.putf('<I', xray.ikflags)
        pwriter.putf('<2f', xray.breakf.force, xray.breakf.torque)
        pwriter.putf('<f', xray.friction)
        world_matrix = obj.matrix_world
        mat = multiply(
            world_matrix,
            bone.matrix_local,
            motions.const.MATRIX_BONE_INVERTED
        )
        b_parent = utils.bone.find_bone_exportable_parent(bone)
        if b_parent:
            mat = multiply(multiply(
                world_matrix,
                b_parent.matrix_local,
                motions.const.MATRIX_BONE_INVERTED
            ).inverted(), mat)
        euler = mat.to_euler('YXZ')
        pwriter.putf('<3f', -euler.x, -euler.z, -euler.y)
        pwriter.putv3f(mat.to_translation())
        pwriter.putf('<f', xray.mass.value)
        pwriter.putv3f(xray.mass.center)
    cwriter.put(fmt.Chunks_v4.S_IKDATA_2, pwriter)

    packed_writer = rw.write.PackedWriter()
    packed_writer.puts(bpy_obj.xray.userdata)
    cwriter.put(fmt.Chunks_v4.S_USERDATA, packed_writer)
    if len(bpy_obj.xray.motionrefs_collection):
        refs = []
        for ref in bpy_obj.xray.motionrefs_collection:
            refs.append(ref.name)
        refs_string = ','.join(refs)
        motion_refs_writer = rw.write.PackedWriter()
        motion_refs_writer.puts(refs_string)
        cwriter.put(fmt.Chunks_v4.S_MOTION_REFS_0, motion_refs_writer)

    # export motions
    if context.export_motions and bpy_obj.xray.motions_collection:
        motion_context = omf.ops.ExportOmfContext()
        motion_context.bpy_arm_obj = bpy_obj
        motion_context.export_mode = 'OVERWRITE'
        motion_context.export_motions = True
        motion_context.export_bone_parts = True
        motion_context.need_motions = True
        motion_context.need_bone_groups = True
        motions_chunked_writer = omf.exp.export_omf(motion_context)
        cwriter.data.extend(motions_chunked_writer.data)


@log.with_context('export-object')
def export_file(bpy_obj, file_path, context):
    log.update(object=bpy_obj.name)
    cwriter = rw.write.ChunkedWriter()
    _export(bpy_obj, cwriter, context)
    rw.utils.save_file(file_path, cwriter)
