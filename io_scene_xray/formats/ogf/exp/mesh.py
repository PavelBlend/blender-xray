# blender modules
import bpy
import bmesh

# addon modules
from . import bone
from . import write
from .... import text
from .... import rw
from .... import log
from .... import utils


def _get_temp_mesh(root_obj, bpy_obj):
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


def _collect_geom(bpy_mesh, mesh, vgroups_map):
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

            if vgroups_map is not None:
                for group_index, weight in loop.vert[weight_layer].items():
                    remap_group_index = vgroups_map.get(group_index, None)
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


def _collect_vgrps(bpy_obj, arm_obj, bones, bones_map):

    if not arm_obj:
        return

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

    return vertex_groups_map


def _export_child(root_obj, bpy_obj, writer, ctx, vgroups_map):

    # get export mesh
    bpy_mesh, mesh = _get_temp_mesh(root_obj, bpy_obj)

    # collect geometry data
    vertices, tris, max_wght = _collect_geom(bpy_mesh, mesh, vgroups_map)

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


def _export_children(
        ctx,
        child_objects,
        root_obj,
        meshes,
        vertex_groups_map,
        remove_child_objects
    ):

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


def _check_uv_maps(bpy_obj):
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


def _check_exp_data(bpy_obj, arm_obj):

    # check vertex weights
    if arm_obj:
        utils.ie.validate_vertex_weights(bpy_obj, arm_obj)

    # check uv-maps
    _check_uv_maps(bpy_obj)


def _separate_by_mats(bpy_obj, child_objects):
    bpy.ops.object.select_all(action='DESELECT')

    # copy mesh-object
    multi_material_mesh = bpy_obj.data.copy()
    multi_material_object = bpy_obj.copy()
    multi_material_object.data = multi_material_mesh

    # link and set active
    utils.version.link_object(multi_material_object)
    utils.version.set_active_object(multi_material_object)

    # create temp empty-object
    temp_parent_object = bpy.data.objects.new('!-temp-parent-object', None)
    utils.version.link_object(temp_parent_object)
    multi_material_object.parent = temp_parent_object

    # separate by materials
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.separate(type='MATERIAL')
    bpy.ops.object.mode_set(mode='OBJECT')

    # collect single material meshes
    for child_object in temp_parent_object.children:
        child_objects.append(child_object)

    # remove temp empty-object
    bpy.data.objects.remove(temp_parent_object)


def _get_mesh_objs(bpy_obj):
    child_objects = []

    if len(bpy_obj.material_slots) > 1:
        # separate mesh-object by materials
        _separate_by_mats(bpy_obj, child_objects)
        remove_child_objects = True

    else:
        child_objects.append(bpy_obj)
        remove_child_objects = False

    return child_objects, remove_child_objects


def scan_mesh(ctx, bpy_obj, root_obj, meshes, bones, bones_map):

    # get armature
    arm_obj = utils.obj.get_armature_object(bpy_obj)

    # check export data
    _check_exp_data(bpy_obj, arm_obj)

    # collect vertex groups
    vertex_groups_map = _collect_vgrps(bpy_obj, arm_obj, bones, bones_map)

    # get mesh-objects
    child_objects, remove_child_objects = _get_mesh_objs(bpy_obj)

    # export
    _export_children(
        ctx,
        child_objects,
        root_obj,
        meshes,
        vertex_groups_map,
        remove_child_objects
    )

    # remove temp meshes
    _remove_child_objs(remove_child_objects, child_objects)
