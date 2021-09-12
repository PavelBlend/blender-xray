# standart modules
import math

# blender modules
import bpy
import mathutils

# addon modules
from . import mesh
from . import bone
from .. import fmt
from ... import xray_io
from ... import utils
from ... import log
from ... import xray_motions
from ... import version_utils


def export_version(chunked_writer):
    chunked_writer.put(
        fmt.Chunks.Object.VERSION,
        xray_io.PackedWriter().putf('H', 0x10)
    )


def get_object_flags(xray):
    if xray is not None:
        flags = xray.flags
    else:
        flags = 0
    return flags


def export_flags(chunked_writer, xray, some_arm):
    flags = get_object_flags(xray)
    if not some_arm is None:
        # 1 - Dynamic
        # 3 - Progressive Dynamic
        if not flags in (1, 3):
            # set Dynamic flag
            # so that it is possible to export to ogf from ActorEditor
            flags = 1
    chunked_writer.put(
        fmt.Chunks.Object.FLAGS,
        xray_io.PackedWriter().putf('I', flags)
    )


def validate_vertex_weights(bpy_obj, arm_obj):
    exportable_bones_names = [
        bpy_bone.name
        for bpy_bone in arm_obj.data.bones
            if bpy_bone.xray.exportable
    ]
    exportable_groups_indices = [
        group.index for group in bpy_obj.vertex_groups if group.name in exportable_bones_names
    ]
    has_ungrouped_vertices = None
    ungrouped_vertices_count = 0
    for vertex in bpy_obj.data.vertices:
        if not len(vertex.groups):
            has_ungrouped_vertices = True
            ungrouped_vertices_count += 1
        else:
            exportable_groups_count = 0
            for vertex_group in vertex.groups:
                if vertex_group.group in exportable_groups_indices:
                    exportable_groups_count += 1
            if not exportable_groups_count:
                has_ungrouped_vertices = True
                ungrouped_vertices_count += 1
    if has_ungrouped_vertices:
        raise utils.AppError('Mesh "{0}" has {1} vertices that are not tied to any exportable bones'.format(
            bpy_obj.data.name, ungrouped_vertices_count
        ))


@log.with_context('export-armature-object')
def _check_bone_names(armature_object):
    bone_names = {}
    bone_duplicates = {}
    for bpy_bone in armature_object.data.bones:
        name = bpy_bone.name
        name_lower = name.lower()
        if bone_names.get(name_lower, None):
            if not bone_duplicates.get(name_lower, None):
                bone_duplicates[name_lower] = [bone_names.get(name_lower), ]
            bone_duplicates[name_lower].append(name)
        else:
            bone_names[name_lower] = name
    if bone_duplicates:
        log.update(object=armature_object.name)
        raise utils.AppError(
            'The object has duplicate bones',
            log.props(bones=tuple(bone_duplicates.values()))
        )


def merge_meshes(mesh_objects):
    merged_mesh = bpy.data.meshes.new('merged_meshes')
    merged_object = bpy.data.objects.new('merged_meshes', merged_mesh)
    verts = []
    faces = []
    uvs = []
    sharp_edges = []
    faces_smooth = []
    materials = []
    vertex_groups = []
    vertex_group_indices = []
    vertex_group_names = {}
    used_vertex_groups = set()
    vert_index_offset = 0
    edge_index_offset = 0
    material_index_offset = 0
    group_index_offset = 0
    active_object = bpy.context.active_object
    temp_name = '!TEMP io_scene_xray'
    for obj in mesh_objects:
        copy_obj = obj.copy()
        copy_obj.name = temp_name
        copy_mesh = obj.data.copy()
        copy_mesh.name = temp_name
        copy_obj.data = copy_mesh
        version_utils.link_object(copy_obj)
        version_utils.set_active_object(copy_obj)
        for mod in copy_obj.modifiers:
            if mod.type == 'ARMATURE':
                continue
            bpy.ops.object.modifier_apply(modifier=mod.name)
        mesh = copy_obj.data
        for material in mesh.materials:
            merged_mesh.materials.append(material)
        for group_index, group in enumerate(copy_obj.vertex_groups):
            index = group_index + group_index_offset
            vertex_group_indices.append(index)
            vertex_group_names[index] = group.name
        for vertex in mesh.vertices:
            verts.append(tuple(vertex.co))
            groups = {}
            for group in vertex.groups:
                index = group.group + group_index_offset
                groups[index] = group.weight
                used_vertex_groups.add(index)
            vertex_groups.append(groups)
        for polygon in mesh.polygons:
            materials.append(polygon.material_index + material_index_offset)
            faces_smooth.append(polygon.use_smooth)
            vert_indices = []
            for vertex_index in polygon.vertices:
                vert_indices.append(vert_index_offset + vertex_index)
            use_sharp = []
            for loop_index in polygon.loop_indices:
                loop = mesh.loops[loop_index]
                edge = mesh.edges[loop.edge_index]
                use_sharp.append(edge.use_edge_sharp)
            sharp_edges.append(use_sharp)
            faces.append(vert_indices)
        uv_layers = mesh.uv_layers
        if len(uv_layers) > 1:
            raise utils.AppError(
                'Object "{}" has more than one UV-map'.format(obj.name)
            )
        uv_layer = uv_layers[0]
        for uv_data in uv_layer.data:
            uvs.extend((uv_data.uv[0], uv_data.uv[1]))
        verts_count = len(mesh.vertices)
        vert_index_offset += verts_count
        materials_count = len(mesh.materials)
        material_index_offset += materials_count
        groups_count = len(copy_obj.vertex_groups)
        group_index_offset += groups_count
        bpy.data.objects.remove(copy_obj)
        bpy.data.meshes.remove(copy_mesh)
    merged_mesh.from_pydata(verts, (), faces)
    merged_mesh.polygons.foreach_set('material_index', materials)
    merged_mesh.polygons.foreach_set('use_smooth', faces_smooth)
    if version_utils.IS_28:
        uv_layer = merged_mesh.uv_layers.new(name='Texture')
    else:
        uv_texture = merged_mesh.uv_textures.new(name='Texture')
        uv_layer = merged_mesh.uv_layers[uv_texture.name]
    uv_layer.data.foreach_set('uv', uvs)
    for polygon_index, polygon in enumerate(merged_mesh.polygons):
        for index, loop_index in enumerate(polygon.loop_indices):
            loop = merged_mesh.loops[loop_index]
            edge = merged_mesh.edges[loop.edge_index]
            edge.use_edge_sharp = sharp_edges[polygon_index][index]
    remap_vertex_group_indices = {}
    group_indices = {}
    group_index = 0
    for index in vertex_group_indices:
        if index in used_vertex_groups:
            name = vertex_group_names[index]
            group_index_by_name = group_indices.get(name, None)
            if group_index_by_name is None:
                group = merged_object.vertex_groups.new(name=name)
                remap_vertex_group_indices[index] = group_index
                group_index += 1
                group_indices[name] = index
            else:
                remap_vertex_group_indices[index] = group_index_by_name
    for vertex_index, vertex_group in enumerate(vertex_groups):
        for group_index, weight in vertex_group.items():
            group_index = remap_vertex_group_indices[group_index]
            group = merged_object.vertex_groups[group_index]
            group.add((vertex_index, ), weight, 'REPLACE')
    merged_mesh.use_auto_smooth = True
    merged_mesh.auto_smooth_angle = math.pi
    version_utils.set_active_object(active_object)
    return merged_object


def export_meshes(chunked_writer, bpy_obj, context, obj_xray):
    mesh_writers = []
    armatures = set()
    materials = set()
    meshes = set()
    uv_maps_names = {}
    bpy_root = bpy_obj
    armature_meshes = set()
    skeletal_obj = None

    def write_mesh(bpy_obj, skeletal_obj=None):
        meshes.add(bpy_obj)
        mesh_writer = xray_io.ChunkedWriter()
        used_material_names = mesh.export_mesh(
            bpy_obj,
            bpy_root,
            mesh_writer,
            context
        )
        mesh_writers.append(mesh_writer)
        for material in bpy_obj.data.materials:
            if not material:
                continue
            if material.name in used_material_names:
                materials.add(material)
                uv_layers = bpy_obj.data.uv_layers
                if len(uv_layers) > 1:
                    raise utils.AppError(
                        'Object "{}" has more than one UV-map'.format(bpy_obj.name)
                    )
                uv_maps_names[material.name] = uv_layers[0].name

    def scan_r(bpy_obj):
        if utils.is_helper_object(bpy_obj):
            return
        if bpy_obj.type == 'MESH':
            if bpy_root.type != 'ARMATURE':
                write_mesh(bpy_obj)
            else:
                armature_meshes.add(bpy_obj)
                for modifier in bpy_obj.modifiers:
                    if (modifier.type == 'ARMATURE') and modifier.object:
                        armatures.add(modifier.object)
        elif bpy_obj.type == 'ARMATURE':
            armatures.add(bpy_obj)
        for child in bpy_obj.children:
            scan_r(child)

    scan_r(bpy_obj)
    if len(armatures) > 1:
        raise utils.AppError(
            'Root object "{}" has more than one armature'.format(bpy_obj.name)
        )
    if armature_meshes:
        if len(armature_meshes) == 1:
            write_mesh(list(armature_meshes)[0])
        else:
            skeletal_obj = merge_meshes(armature_meshes)
            write_mesh(skeletal_obj)
            mesh_names = [mesh.name for mesh in armature_meshes]
            log.warn(
                'mesh-objects have been merged',
                objects=mesh_names
            )
    if not mesh_writers:
        raise utils.AppError(
            'Root object "{}" has no meshes'.format(bpy_obj.name)
        )
    if len(mesh_writers) > 1 and len(armatures):
        raise utils.AppError(
            'Skeletal object "{}" has more than one mesh'.format(bpy_obj.name)
        )

    if len(armatures) == 1:
        for mesh_obj in meshes:
            validate_vertex_weights(mesh_obj, list(armatures)[0])

    bone_writers = []
    root_bones = []
    armatures = list(armatures)
    if armatures:
        bpy_arm_obj = armatures[0]
        _check_bone_names(bpy_arm_obj)
        bonemap = {}
        edit_mode_matrices = {}
        with version_utils.using_active_object(bpy_arm_obj), utils.using_mode('EDIT'):
            for bone_ in bpy_arm_obj.data.edit_bones:
                edit_mode_matrices[bone_.name] = bone_.matrix
        for bone_ in bpy_arm_obj.data.bones:
            if not utils.is_exportable_bone(bone_):
                continue
            real_parent = utils.find_bone_exportable_parent(bone_)
            if not real_parent:
                root_bones.append(bone_.name)
            bone.export_bone(
                bpy_arm_obj, bone_, bone_writers, bonemap,
                edit_mode_matrices, context.multiply
            )

        invalid_bones = []
        has_bone_groups = False
        if len(bpy_arm_obj.pose.bone_groups):
            for bone_ in bpy_arm_obj.pose.bones:
                xray = bpy_arm_obj.data.bones[bone_.name].xray
                if xray.exportable:
                    if bone_.bone_group is None:
                        invalid_bones.append(bone_.name)
                    else:
                        has_bone_groups = True
        if invalid_bones and has_bone_groups:
            raise utils.AppError(
                'Invalid bone parts: not all bones are tied to the Bone Part',
                log.props(bones=invalid_bones)
            )
    if len(root_bones) > 1:
        raise utils.AppError(
            'Invalid armature object "{}". Has more than one parent: {}'.format(
                bpy_arm_obj.name, root_bones
        ))

    arm_list = list(armatures)

    # take care of static objects
    some_arm = arm_list[0] if arm_list else None
    if some_arm:
        if some_arm.scale != mathutils.Vector((1.0, 1.0, 1.0)):
            raise utils.AppError(
                'Armature object "{}" has incorrect scale.'
                'The scale must be (1.0, 1.0, 1.0).'.format(some_arm.name)
            )
    export_flags(chunked_writer, obj_xray, some_arm)

    msw = xray_io.ChunkedWriter()
    idx = 0
    for mesh_writer in mesh_writers:
        msw.put(idx, mesh_writer)
        idx += 1

    chunked_writer.put(fmt.Chunks.Object.MESHES, msw)

    if skeletal_obj:
        merged_mesh = skeletal_obj.data
        bpy.data.objects.remove(skeletal_obj)
        bpy.data.meshes.remove(merged_mesh)

    return materials, bone_writers, some_arm, bpy_root, uv_maps_names


def export_surfaces(chunked_writer, context, materials, uv_map_names):
    sfw = xray_io.PackedWriter()
    sfw.putf('I', len(materials))
    for material in materials:
        sfw.puts(material.name)
        if hasattr(material, 'xray'):
            sfw.puts(
                material.xray.eshader
            ).puts(
                material.xray.cshader
            ).puts(
                material.xray.gamemtl
            )
        else:
            sfw.puts('').puts('').puts('')
        tx_name = ''
        if version_utils.IS_28:
            if material.use_nodes:
                tex_nodes = []
                for node in material.node_tree.nodes:
                    if node.type in version_utils.IMAGE_NODES:
                        tex_nodes.append(node)
                if len(tex_nodes) == 1:
                    tex_node = tex_nodes[0]
                    if tex_node.image:
                        if context.texname_from_path:
                            tx_name = utils.gen_texture_name(
                                tex_node.image, context.textures_folder
                            )
                            if tex_node.type == 'TEX_ENVIRONMENT':
                                log.warn(
                                    'material "{}" has incorrect image node type (Environment Texture)'.format(material.name),
                                    material_name=material.name,
                                    node_name=tex_node.name,
                                )
                        else:
                            tx_name = tex_node.name
                elif len(tex_nodes) > 1:
                    raise utils.AppError(
                        'Material "{}" has more than one texture.'.format(
                            material.name
                    ))
            else:
                raise utils.AppError('material "{}" does not use nodes'.format(material.name))
        else:
            if material.active_texture:
                if context.texname_from_path:
                    tx_name = utils.gen_texture_name(
                        material.active_texture.image, context.textures_folder
                    )
                else:
                    tx_name = material.active_texture.name
        sfw.puts(tx_name)
        if version_utils.IS_28:
            sfw.puts(uv_map_names[material.name])
        else:
            slot = material.texture_slots[material.active_texture_index]
            sfw.puts(slot.uv_layer if slot else '')
        if hasattr(material, 'xray'):
            sfw.putf('I', material.xray.flags)
        else:
            sfw.putf('I', 0)
        sfw.putf('I', 0x112).putf('I', 1)
    chunked_writer.put(fmt.Chunks.Object.SURFACES2, sfw)


def export_bones(chunked_writer, bone_writers):
    if bone_writers:
        writer = xray_io.ChunkedWriter()
        idx = 0
        for bone_writer in bone_writers:
            writer.put(idx, bone_writer)
            idx += 1
        chunked_writer.put(fmt.Chunks.Object.BONES1, writer)


def export_user_data(chunked_writer, xray):
    if xray.userdata:
        chunked_writer.put(
            fmt.Chunks.Object.USERDATA,
            xray_io.PackedWriter().puts(
                '\r\n'.join(xray.userdata.splitlines())
            )
        )


def export_loddef(chunked_writer, xray):
    if xray.lodref:
        chunked_writer.put(
            fmt.Chunks.Object.LOD_REF,
            xray_io.PackedWriter().puts(xray.lodref)
        )


def export_motions(chunked_writer, some_arm, context, bpy_obj):
    if some_arm and context.export_motions:
        motions = [motion.name for motion in bpy_obj.xray.motions_collection]
        motions = set(motions)
        motions = list(motions)
        motions.sort()
        acts = []
        for act_name in motions:
            act = bpy.data.actions.get(act_name, None)
            if act:
                acts.append(act)
            else:
                log.warn(
                    'Cannot find action "{0}" in object "{1}"'.format(
                        act_name, bpy_obj.name
                    ),
                )
        writer = xray_io.PackedWriter()
        xray_motions.export_motions(writer, acts, some_arm)
        if writer.data:
            chunked_writer.put(fmt.Chunks.Object.MOTIONS, writer)


def export_partitions(chunked_writer, some_arm):
    if some_arm and some_arm.pose.bone_groups:
        exportable_bones = tuple(
            bone_
            for bone_ in some_arm.pose.bones
            if utils.is_exportable_bone(some_arm.data.bones[bone_.name])
        )
        all_groups = (
            (group.name, tuple(
                bone_.name
                for bone_ in exportable_bones
                if bone_.bone_group == group
            ))
            for group in some_arm.pose.bone_groups
        )
        non_empty_groups = tuple(
            group
            for group in all_groups
            if group[1]
        )
        if non_empty_groups:
            writer = xray_io.PackedWriter()
            writer.putf('I', len(non_empty_groups))
            for name, bones in non_empty_groups:
                writer.puts(name)
                writer.putf('I', len(bones))
                for bone_ in bones:
                    writer.puts(bone_.lower())
            chunked_writer.put(fmt.Chunks.Object.PARTITIONS1, writer)


def export_motion_refs(chunked_writer, xray, context):
    motionrefs = xray.motionrefs_collection
    if motionrefs:
        if xray.motionrefs:
            log.warn('MotionRefs: skipped legacy data', data=xray.motionrefs)
        if context.soc_sgroups:
            refs = ','.join(ref.name for ref in motionrefs)
            chunked_writer.put(
                fmt.Chunks.Object.MOTION_REFS,
                xray_io.PackedWriter().puts(refs)
            )
        else:
            writer = xray_io.PackedWriter()
            writer.putf('I', len(motionrefs))
            for ref in motionrefs:
                writer.puts(ref.name)
            chunked_writer.put(fmt.Chunks.Object.SMOTIONS3, writer)
    elif xray.motionrefs:
        chunked_writer.put(
            fmt.Chunks.Object.MOTION_REFS,
            xray_io.PackedWriter().puts(xray.motionrefs)
        )


def export_transform(chunked_writer, bpy_root):
    root_matrix = bpy_root.matrix_world
    if root_matrix != mathutils.Matrix.Identity(4):
        writer = xray_io.PackedWriter()
        writer.putv3f(root_matrix.to_translation())
        writer.putv3f(root_matrix.to_euler('YXZ'))
        chunked_writer.put(fmt.Chunks.Object.TRANSFORM, writer)


def export_revision(chunked_writer, xray):
    owner, ctime, moder, mtime = utils.get_revision_data(xray.revision)
    writer = xray_io.PackedWriter()
    writer.puts(owner)
    writer.putf('I', ctime)
    writer.puts(moder)
    writer.putf('I', mtime)
    chunked_writer.put(fmt.Chunks.Object.REVISION, writer)


# @utils.time_log()
def export_main(bpy_obj, chunked_writer, context):
    xray = bpy_obj.xray if hasattr(bpy_obj, 'xray') else None

    export_version(chunked_writer)
    materials, bone_writers, some_arm, bpy_root, uv_map_names = export_meshes(
        chunked_writer, bpy_obj, context, xray
    )
    export_surfaces(chunked_writer, context, materials, uv_map_names)
    export_bones(chunked_writer, bone_writers)
    export_user_data(chunked_writer, xray)
    export_loddef(chunked_writer, xray)
    export_motions(chunked_writer, some_arm, context, bpy_obj)
    export_partitions(chunked_writer, some_arm)
    export_motion_refs(chunked_writer, xray, context)
    export_transform(chunked_writer, bpy_root)
    export_revision(chunked_writer, xray)
