# blender modules
import bpy
import bmesh
import mathutils

# addon modules
from . import ie
from . import obj
from . import version
from .. import log
from .. import text


def convert_object_to_space_bmesh(
        bpy_obj,
        loc_space,
        rot_space,
        scl_space,
        split_normals=False,
        mods=None
    ):

    mesh = bmesh.new()
    exportable_obj = bpy_obj
    temp_obj = None

    # set sharp edges by face smoothing
    if split_normals and version.has_set_normals_from_faces():
        temp_mesh = bpy_obj.data.copy()
        temp_obj = bpy_obj.copy()
        temp_obj.data = temp_mesh
        for polygon in temp_mesh.polygons:
            if polygon.use_smooth:
                continue
            for loop_index in polygon.loop_indices:
                loop = temp_mesh.loops[loop_index]
                edge = temp_mesh.edges[loop.edge_index]
                edge.use_edge_sharp = True
        version.link_object(temp_obj)
        bpy.ops.object.select_all(action='DESELECT')
        version.set_active_object(temp_obj)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.set_normals_from_faces()
        bpy.ops.object.mode_set(mode='OBJECT')
        exportable_obj = temp_obj

    # apply shape keys
    if exportable_obj.data.shape_keys:
        if not temp_obj:
            temp_mesh = exportable_obj.data.copy()
            temp_obj = exportable_obj.copy()
            temp_obj.data = temp_mesh
            version.link_object(temp_obj)
            version.set_active_object(temp_obj)
            exportable_obj = temp_obj
        temp_obj.shape_key_add(name='last_shape_key', from_mix=True)
        for shape_key in temp_mesh.shape_keys.key_blocks:
            temp_obj.shape_key_remove(shape_key)

    # apply modifiers
    if mods:
        if not temp_obj:
            temp_mesh = exportable_obj.data.copy()
            temp_obj = exportable_obj.copy()
            temp_obj.data = temp_mesh
            version.link_object(temp_obj)
            version.set_active_object(temp_obj)
            exportable_obj = temp_obj
        for mod in mods:
            obj.apply_obj_modifier(mod)

    mesh.from_mesh(exportable_obj.data)

    # apply mesh transforms
    loc_mat, rot_mat, scl_world = ie.get_object_world_matrix(bpy_obj)

    loc = version.multiply(loc_space.inverted(), loc_mat)
    rot = version.multiply(rot_space.inverted(), rot_mat)

    loc_rot = version.multiply(loc, rot)
    scl_mesh = mathutils.Vector()
    scl_mesh.x = scl_world.x / scl_space.x
    scl_mesh.y = scl_world.y / scl_space.y
    scl_mesh.z = scl_world.z / scl_space.z

    scl = mathutils.Vector()
    scl.x = scl_world.x * scl_space.x
    scl.y = scl_world.y * scl_space.y
    scl.z = scl_world.z * scl_space.z

    bmesh.ops.scale(mesh, vec=scl_mesh, verts=mesh.verts)
    mesh.transform(loc_rot)
    bmesh.ops.scale(mesh, vec=scl_space, verts=mesh.verts)

    # flip normals
    need_flip = False
    for scale_component in (*scl_space, *scl_mesh):
        if scale_component < 0:
            need_flip = not need_flip
    if need_flip:
        bmesh.ops.reverse_faces(mesh, faces=mesh.faces)

    fix_ensure_lookup_table(mesh.verts)

    # remove temp mesh object
    if temp_obj:
        bpy.data.objects.remove(temp_obj)
        bpy.data.meshes.remove(temp_mesh)

    return mesh


def fix_ensure_lookup_table(bm_sequence):
    if hasattr(bm_sequence, 'ensure_lookup_table'):
        bm_sequence.ensure_lookup_table()


def set_bound_coord(bound, current, compare_fun):
    bound.x = compare_fun(bound.x, current.x)
    bound.y = compare_fun(bound.y, current.y)
    bound.z = compare_fun(bound.z, current.z)


def calculate_mesh_bbox(verts, mat=mathutils.Matrix()):
    fix_ensure_lookup_table(verts)
    multiply = version.get_multiply()
    bbox_min = multiply(mat, verts[0].co).copy()
    bbox_max = bbox_min.copy()

    for vertex in verts:
        set_bound_coord(bbox_min, multiply(mat, vertex.co), min)
        set_bound_coord(bbox_max, multiply(mat, vertex.co), max)

    return bbox_min, bbox_max


def calculate_mesh_bsphere(bbox, vertices, mat=mathutils.Matrix()):
    center = (bbox[0] + bbox[1]) / 2
    _delta = bbox[1] - bbox[0]
    max_radius = max(abs(_delta.x), abs(_delta.y), abs(_delta.z)) / 2
    multiply = version.get_multiply()

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
        if obj.is_helper_object(bpy_obj):
            return
        if (bpy_obj.type == 'MESH') and bpy_obj.data.vertices:
            meshes.append(bpy_obj)
        for child in bpy_obj.children:
            scan_meshes(child, meshes)

    def scan_meshes_using_cache(bpy_obj, meshes, cache):
        if obj.is_helper_object(bpy_obj):
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
    loc_space, rot_space, scl_space = ie.get_object_world_matrix(bpy_obj)
    for bpy_mesh in meshes:
        mat_world = mathutils.Matrix.Identity(4)
        if cache:
            if cache.bounds.get(bpy_mesh.name, None):
                bbx, center, radius = cache.bounds[bpy_mesh.name]
            else:
                if apply_transforms:
                    mesh = convert_object_to_space_bmesh(
                        bpy_mesh,
                        mathutils.Matrix.Identity(4),
                        mathutils.Matrix.Identity(4),
                        mathutils.Vector((1.0, 1.0, 1.0))
                    )
                else:
                    mesh = convert_object_to_space_bmesh(
                        bpy_mesh,
                        loc_space,
                        rot_space,
                        scl_space
                    )
                bbx = calculate_mesh_bbox(mesh.verts, mat=mat_world)
                center, radius = calculate_mesh_bsphere(
                    bbx,
                    mesh.verts,
                    mat=mat_world
                )
                cache.bounds[bpy_mesh.name] = bbx, center, radius
        else:
            if apply_transforms:
                mesh = convert_object_to_space_bmesh(
                    bpy_mesh,
                    mathutils.Matrix.Identity(4),
                    mathutils.Matrix.Identity(4),
                    mathutils.Vector((1.0, 1.0, 1.0))
                )
            else:
                mesh = convert_object_to_space_bmesh(
                    bpy_mesh,
                    loc_space,
                    rot_space,
                    scl_space
                )
            bbx = calculate_mesh_bbox(mesh.verts, mat=mat_world)
            center, radius = calculate_mesh_bsphere(
                bbx,
                mesh.verts,
                mat=mat_world
            )

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


def weights_top(weights, count):
    return sorted(weights, key=lambda x: x[1], reverse=True)[0 : count]


def _unhide_faces(bpy_obj):
    for face in bpy_obj.data.polygons:
        face.hide = False
        face.select = False


def _unhide_edges(bpy_obj):
    for edge in bpy_obj.data.edges:
        edge.hide = False
        edge.select = False


def check_zero_weight_verts(bpy_obj):
    _unhide_faces(bpy_obj)
    _unhide_edges(bpy_obj)

    zero_vert_count = 0

    for vert in bpy_obj.data.vertices:

        # unhide vertex
        vert.hide = False

        # calculate total weight
        total_weight = 0.0
        for group in vert.groups:
            total_weight += group.weight

        # select
        if total_weight:
            vert.select = False
        else:
            vert.select = True
            zero_vert_count += 1

    # report
    if zero_vert_count:
        raise log.AppError(
            text.error.zero_weights,
            log.props(object=bpy_obj.name, vertices_count=zero_vert_count)
        )
