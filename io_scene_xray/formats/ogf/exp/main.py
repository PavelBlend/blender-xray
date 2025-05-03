# blender modules
import bpy
import bmesh

# addon modules
from . import bone
from . import write
from .. import fmt
from .... import text
from .... import inspect
from .... import rw
from .... import log
from .... import utils


def get_temp_mesh(root_obj, bpy_obj):
    modifiers = [
        mod
        for mod in bpy_obj.modifiers
            if mod.type != 'ARMATURE' and mod.show_viewport
    ]

    mesh = utils.mesh.convert_object_to_space_bmesh(
        bpy_obj,
        root_obj,
        mods=modifiers
    )

    bmesh.ops.triangulate(mesh, faces=mesh.faces)

    bpy_mesh = bpy.data.meshes.new('.export-ogf')
    if not utils.version.IS_41:
        bpy_mesh.use_auto_smooth = bpy_obj.data.use_auto_smooth
        bpy_mesh.auto_smooth_angle = bpy_obj.data.auto_smooth_angle

    mesh.to_mesh(bpy_mesh)

    return bpy_mesh, mesh


def collect_geom(bpy_mesh, mesh, vertex_groups_map):
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

    return vertices, triangles, vertex_max_weights


def _export_child(root_obj, bpy_obj, writer, ctx, vgroups_map):

    # get export mesh
    bpy_mesh, mesh = get_temp_mesh(root_obj, bpy_obj)

    # collect geometry data
    vertices, tris, max_wght = collect_geom(bpy_mesh, mesh, vgroups_map)

    # write
    write.write_child(bpy_obj, writer, ctx, mesh, vertices, tris, max_wght)

    # remove temp mesh
    bpy.data.meshes.remove(bpy_mesh)
    mesh.free()


def _remove_child_objs(remove_child_objects, child_objects):
    if remove_child_objects:
        for child_object in child_objects:
            child_mesh = child_object.data
            bpy.data.objects.remove(child_object)
            bpy.data.meshes.remove(child_mesh)


def _scan_mesh(ctx, bpy_obj, root_obj, meshes, bones, bones_map):
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
        bpy_bone = arm_obj.data.bones.get(group.name, None)

        if bpy_bone is None:
            continue

        if not utils.bone.is_exportable_bone(bpy_bone):
            continue

        vertex_groups_map[group_index] = bone.reg_bone(
            bones,
            bones_map,
            bpy_bone,
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

        try:
            _export_child(
                root_obj,
                child_object,
                mesh_writer,
                ctx,
                vertex_groups_map
            )
        except log.AppError as err:
            _remove_child_objs(remove_child_objects, child_objects)
            raise err

        meshes.append(mesh_writer)

    _remove_child_objs(remove_child_objects, child_objects)


def _scan_arm(bpy_obj, arms, bones, bones_map):
    arms.append(bpy_obj)

    for bpy_bone in bpy_obj.data.bones:

        if not utils.bone.is_exportable_bone(bpy_bone):
            continue

        bone.reg_bone(bones, bones_map, bpy_bone, bpy_obj)


def _scan_obj(bpy_obj, root_obj, meshes, arms, bones, bones_map, ctx):
    if utils.obj.is_helper_object(bpy_obj):
        return

    # scan mesh
    if bpy_obj.type == 'MESH':
        _scan_mesh(ctx, bpy_obj, root_obj, meshes, bones, bones_map)

    # scan armature
    elif bpy_obj.type == 'ARMATURE':
        _scan_arm(bpy_obj, arms, bones, bones_map)


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


def _export_main(root_obj, writer, ctx):

    meshes = []
    arms = []
    bones = []
    bones_map = {}

    exp_objs = utils.obj.get_exp_objs(ctx, root_obj)
    for obj in exp_objs:
        _scan_obj(obj, root_obj, meshes, arms, bones, bones_map, ctx)

    # get armature
    arm_obj = _get_arm(root_obj, arms)

    # check bone names
    inspect.bone.check_bone_names(arm_obj)

    # get armature scale
    scale = _get_arm_scale(root_obj, arm_obj)

    # write
    write.write_skeleton(root_obj, arm_obj, writer, ctx, meshes, bones, scale)


@log.with_context('export-ogf')
@utils.stats.timer
def export_file(bpy_obj, file_path, ctx):
    utils.stats.status('Export File', file_path)
    log.update(object=bpy_obj.name)

    ogf_writer = rw.write.ChunkedWriter()
    _export_main(bpy_obj, ogf_writer, ctx)
    rw.utils.save_file(file_path, ogf_writer)
