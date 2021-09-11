# standart modules
import math

# blender modules
import bpy
import bmesh
import mathutils

# addon modules
from . import fmt
from .. import xray_io
from .. import utils
from .. import version_utils
from .. import xray_motions


multiply = version_utils.get_multiply()


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
                mesh = utils.convert_object_to_space_bmesh(bpy_mesh, mat_world)
                bbx = utils.calculate_mesh_bbox(mesh.verts, mat=mat_world)
                center, radius = calculate_mesh_bsphere(bbx, mesh.verts, mat=mat_world)
                cache.bounds[bpy_mesh.name] = bbx, center, radius
        else:
            if apply_transforms:
                mat_world = bpy_mesh.matrix_world
            else:
                mat_world = mathutils.Matrix()
            mesh = utils.convert_object_to_space_bmesh(bpy_mesh, mat_world)
            bbx = utils.calculate_mesh_bbox(mesh.verts, mat=mat_world)
            center, radius = calculate_mesh_bsphere(bbx, mesh.verts, mat=mat_world)

        if bbox is None:
            bbox = bbx
        else:
            for i in range(3):
                bbox[0][i] = min(bbox[0][i], bbx[0][i])
                bbox[1][i] = max(bbox[1][i], bbx[1][i])
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
        for key, val in dic.items():
            if (key != skip) and (val > max_val):
                max_val = val
                max_key = key
        return max_key, max_val

    key0, val0 = top_one(dic)
    key1, val1 = top_one(dic, key0)
    return {key0: val0, key1: val1}


def pw_v3f(vec):
    return vec[0], vec[2], vec[1]


def _export_child(bpy_obj, cwriter, context, vgm):
    mesh = utils.convert_object_to_space_bmesh(bpy_obj, mathutils.Matrix.Identity(4))
    bbox = utils.calculate_mesh_bbox(mesh.verts)
    bsph = calculate_mesh_bsphere(bbox, mesh.verts)
    bmesh.ops.triangulate(mesh, faces=mesh.faces)
    bpy_data = bpy.data.meshes.new('.export-ogf')
    bpy_data.use_auto_smooth = True
    bpy_data.auto_smooth_angle = math.pi
    bpy_data.calc_normals_split()
    mesh.to_mesh(bpy_data)

    cwriter.put(
        fmt.HEADER,
        xray_io.PackedWriter()
        .putf('B', 4)  # ogf version
        .putf('B', fmt.ModelType_v4.SKELETON_GEOMDEF_ST)
        .putf('H', 0)  # shader id
        .putf('fff', *pw_v3f(bbox[0])).putf('fff', *pw_v3f(bbox[1]))
        .putf('fff', *pw_v3f(bsph[0])).putf('f', bsph[1])
    )

    material = bpy_obj.data.materials[0]
    texture = None
    if version_utils.IS_28:
        if material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type in version_utils.IMAGE_NODES:
                    texture = node
        else:
            raise utils.AppError('Material "{}" cannot use nodes.'.format(material.name))
    else:
        texture = material.active_texture
    cwriter.put(
        fmt.Chunks_v4.TEXTURE,
        xray_io.PackedWriter()
        .puts(
            utils.gen_texture_name(texture.image, context.textures_folder)
            if context.texname_from_path else
            texture.name
        )
        .puts(material.xray.eshader)
    )

    bml_uv = mesh.loops.layers.uv.active
    bml_vw = mesh.verts.layers.deform.verify()
    bpy_data.calc_tangents(uvmap=bml_uv.name)
    vertices = []
    indices = []
    vmap = {}
    for face in mesh.faces:
        face_indices = []
        for loop_index, loop in enumerate(face.loops):
            data_loop = bpy_data.loops[face.index * 3 + loop_index]
            uv = loop[bml_uv].uv
            vtx = (
                loop.vert.index,
                loop.vert.co.to_tuple(),
                data_loop.normal.to_tuple(),
                data_loop.tangent.to_tuple(),
                data_loop.bitangent.normalized().to_tuple(),
                (uv[0], 1 - uv[1]),
            )
            vertex_index = vmap.get(vtx)
            if vertex_index is None:
                vmap[vtx] = vertex_index = len(vertices)
                vertices.append(vtx)
            face_indices.append(vertex_index)
        indices.append(face_indices)

    vwmx = 0
    for vertex in mesh.verts:
        vwc = len(vertex[bml_vw])
        if vwc > vwmx:
            vwmx = vwc

    utils.fix_ensure_lookup_table(mesh.verts)
    pwriter = xray_io.PackedWriter()
    if vwmx == 1:
        pwriter.putf('II', fmt.VertexFormat.FVF_1L, len(vertices))
        for vertex in vertices:
            weights = mesh.verts[vertex[0]][bml_vw]
            pwriter.putf('fff', *pw_v3f(vertex[1]))
            pwriter.putf('fff', *pw_v3f(vertex[2]))
            pwriter.putf('fff', *pw_v3f(vertex[3]))
            pwriter.putf('fff', *pw_v3f(vertex[4]))
            pwriter.putf('ff', *vertex[5])
            pwriter.putf('I', vgm[weights.keys()[0]])
    else:
        if vwmx != 2:
            print('warning: vwmx=%i' % vwmx)
        pwriter.putf('II', fmt.VertexFormat.FVF_2L, len(vertices))
        for vertex in vertices:
            weights = mesh.verts[vertex[0]][bml_vw]
            if len(weights) > 2:
                weights = top_two(weights)
            weight = 0
            if len(weights) == 2:
                first = True
                weight0 = 0
                for vgi in weights.keys():
                    pwriter.putf('H', vgm[vgi])
                    if first:
                        weight0 = weights[vgi]
                        first = False
                    else:
                        weight = 1 - (weight0 / (weight0 + weights[vgi]))
            elif len(weights) == 1:
                for vgi in [vgm[_] for _ in weights.keys()]:
                    pwriter.putf('HH', vgi, vgi)
            else:
                raise Exception('oops: %i %s' % (len(weights), weights.keys()))
            pwriter.putf('fff', *pw_v3f(vertex[1]))
            pwriter.putf('fff', *pw_v3f(vertex[2]))
            pwriter.putf('fff', *pw_v3f(vertex[3]))
            pwriter.putf('fff', *pw_v3f(vertex[4]))
            pwriter.putf('f', weight)
            pwriter.putf('ff', *vertex[5])
    cwriter.put(fmt.Chunks_v4.VERTICES, pwriter)

    pwriter = xray_io.PackedWriter()
    pwriter.putf('I', 3 * len(indices))
    for face in indices:
        pwriter.putf('HHH', face[0], face[2], face[1])
    cwriter.put(fmt.Chunks_v4.INDICES, pwriter)


def get_ode_ik_limits(value_1, value_2):
    # swap special for ODE
    min_value = min(-value_1, -value_2)
    max_value = max(-value_1, -value_2)
    return min_value, max_value


def _export(bpy_obj, cwriter, context):
    bbox, bsph = calculate_bbox_and_bsphere(bpy_obj)
    if bpy_obj.xray.motionrefs:
        model_type = fmt.ModelType_v4.SKELETON_ANIM
    else:
        model_type = fmt.ModelType_v4.SKELETON_RIGID
    cwriter.put(
        fmt.HEADER,
        xray_io.PackedWriter()
        .putf('B', 4)  # ogf version
        .putf('B', model_type)
        .putf('H', 0)  # shader id
        .putf('fff', *pw_v3f(bbox[0])).putf('fff', *pw_v3f(bbox[1]))
        .putf('fff', *pw_v3f(bsph[0])).putf('f', bsph[1])
    )

    cwriter.put(
        fmt.Chunks_v4.S_DESC,
        xray_io.PackedWriter()
        .puts(bpy_obj.name)    # source file
        .puts('blender')    # build name
        .putf('I', 0)    # build time
        .puts('')    # owner name
        .putf('I', 0)    # create time
        .puts('')    # modifer name
        .putf('I', 0)    # modification time
    )

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
            vgm = {}
            for modifier in bpy_obj.modifiers:
                if (modifier.type == 'ARMATURE') and modifier.object:
                    for i, group in enumerate(bpy_obj.vertex_groups):
                        bone = modifier.object.data.bones.get(group.name, None)
                        if bone is None:
                            raise utils.AppError(
                                'bone "%s" not found in armature "%s" (for object "%s")' % (
                                    group.name, modifier.object.name, bpy_obj.name,
                                ),
                            )
                        vgm[i] = reg_bone(bone, modifier.object)
                    break  # use only first armature modifier
            mwriter = xray_io.ChunkedWriter()
            _export_child(bpy_obj, mwriter, context, vgm)
            meshes.append(mwriter)
        elif bpy_obj.type == 'ARMATURE':
            for bone in bpy_obj.data.bones:
                if not utils.is_exportable_bone(bone):
                    continue
                reg_bone(bone, bpy_obj)
        for child in bpy_obj.children:
            scan_r(child)

    scan_r(bpy_obj)

    ccw = xray_io.ChunkedWriter()
    idx = 0
    for mwriter in meshes:
        ccw.put(idx, mwriter)
        idx += 1
    cwriter.put(fmt.Chunks_v4.CHILDREN, ccw)

    pwriter = xray_io.PackedWriter()
    pwriter.putf('I', len(bones))
    for bone, _ in bones:
        b_parent = utils.find_bone_exportable_parent(bone)
        pwriter.puts(bone.name)
        pwriter.puts(b_parent.name if b_parent else '')
        xray = bone.xray
        pwriter.putf('fffffffff', *xray.shape.box_rot)
        pwriter.putf('fff', *xray.shape.box_trn)
        pwriter.putf('fff', *xray.shape.box_hsz)
    cwriter.put(fmt.Chunks_v4.S_BONE_NAMES, pwriter)

    pwriter = xray_io.PackedWriter()
    for bone, obj in bones:
        pbone = obj.pose.bones[bone.name]
        xray = bone.xray
        pwriter.putf('I', 0x1)  # version
        pwriter.puts(xray.gamemtl)
        pwriter.putf('H', int(xray.shape.type))
        pwriter.putf('H', xray.shape.flags)
        pwriter.putf('fffffffff', *xray.shape.box_rot)
        pwriter.putf('fff', *xray.shape.box_trn)
        pwriter.putf('fff', *xray.shape.box_hsz)
        pwriter.putf('fff', *xray.shape.sph_pos)
        pwriter.putf('f', xray.shape.sph_rad)
        pwriter.putf('fff', *xray.shape.cyl_pos)
        pwriter.putf('fff', *xray.shape.cyl_dir)
        pwriter.putf('f', xray.shape.cyl_hgh)
        pwriter.putf('f', xray.shape.cyl_rad)
        pwriter.putf('I', int(xray.ikjoint.type))

        # x axis
        x_min, x_max = get_ode_ik_limits(
            xray.ikjoint.lim_x_min,
            xray.ikjoint.lim_x_max
        )
        pwriter.putf('ff', x_min, x_max)
        pwriter.putf('ff', xray.ikjoint.lim_x_spr, xray.ikjoint.lim_x_dmp)

        # y axis
        y_min, y_max = get_ode_ik_limits(
            xray.ikjoint.lim_y_min,
            xray.ikjoint.lim_y_max
        )
        pwriter.putf('ff', y_min, y_max)
        pwriter.putf('ff', xray.ikjoint.lim_y_spr, xray.ikjoint.lim_y_dmp)

        # z axis
        z_min, z_max = get_ode_ik_limits(
            xray.ikjoint.lim_z_min,
            xray.ikjoint.lim_z_max
        )
        pwriter.putf('ff', z_min, z_max)
        pwriter.putf('ff', xray.ikjoint.lim_z_spr, xray.ikjoint.lim_z_dmp)

        pwriter.putf('ff', xray.ikjoint.spring, xray.ikjoint.damping)
        pwriter.putf('I', xray.ikflags)
        pwriter.putf('ff', xray.breakf.force, xray.breakf.torque)
        pwriter.putf('f', xray.friction)
        mwriter = obj.matrix_world
        mat = multiply(mwriter, bone.matrix_local, xray_motions.MATRIX_BONE_INVERTED)
        b_parent = utils.find_bone_exportable_parent(bone)
        if b_parent:
            mat = multiply(multiply(
                mwriter, b_parent.matrix_local, xray_motions.MATRIX_BONE_INVERTED
            ).inverted(), mat)
        euler = mat.to_euler('YXZ')
        pwriter.putf('fff', -euler.x, -euler.z, -euler.y)
        pwriter.putf('fff', *pw_v3f(mat.to_translation()))
        pwriter.putf('ffff', xray.mass.value, *pw_v3f(xray.mass.center))
    cwriter.put(fmt.Chunks_v4.S_IKDATA, pwriter)

    cwriter.put(fmt.Chunks_v4.S_USERDATA, xray_io.PackedWriter().puts(bpy_obj.xray.userdata))
    if bpy_obj.xray.motionrefs:
        cwriter.put(fmt.Chunks_v4.S_MOTION_REFS_0, xray_io.PackedWriter().puts(bpy_obj.xray.motionrefs))


def export_file(bpy_obj, fpath, context):
    cwriter = xray_io.ChunkedWriter()
    _export(bpy_obj, cwriter, context)
    utils.save_file(fpath, cwriter)
