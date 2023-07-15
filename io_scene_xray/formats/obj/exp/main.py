# blender modules
import bpy
import mathutils

# addon modules
from . import mesh
from . import bone
from .. import fmt
from ... import motions
from .... import rw
from .... import text
from .... import utils
from .... import log


def export_version(chunked_writer):
    packed_writer = rw.write.PackedWriter()
    packed_writer.putf('<H', fmt.CURRENT_OBJECT_VERSION)
    chunked_writer.put(fmt.Chunks.Object.VERSION, packed_writer)


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
        if flags & ~0x40 not in (1, 3):
            # set Dynamic flag
            # so that it is possible to export to ogf from ActorEditor
            flags = 1 | (flags & 0x40)
            log.warn(
                text.warn.object_set_dynamic,
                object=xray.id_data.name,
                has_type=fmt.type_names[xray.flags_simple],
                save_as=fmt.type_names[fmt.DY]
            )
    packed_writer = rw.write.PackedWriter()
    packed_writer.putf('<I', flags)
    chunked_writer.put(fmt.Chunks.Object.FLAGS, packed_writer)


def validate_vertex_weights(bpy_obj, arm_obj):
    exportable_bones_names = [
        bpy_bone.name
        for bpy_bone in arm_obj.data.bones
            if bpy_bone.xray.exportable
    ]
    exportable_groups_indices = [
        group.index
        for group in bpy_obj.vertex_groups
            if group.name in exportable_bones_names
    ]

    has_ungrouped_verts = None
    ungrouped_verts_count = 0

    has_nonexp_vert_groups = None
    nonexp_group_verts_count = 0

    for vertex in bpy_obj.data.vertices:

        if len(vertex.groups):
            exportable_groups_count = 0
            for vertex_group in vertex.groups:
                if vertex_group.group in exportable_groups_indices:
                    exportable_groups_count += 1
            if not exportable_groups_count:
                has_nonexp_vert_groups = True
                nonexp_group_verts_count += 1

        else:
            has_ungrouped_verts = True
            ungrouped_verts_count += 1

    if has_ungrouped_verts:
        raise log.AppError(
            text.error.object_ungroupped_verts,
            log.props(
                object=bpy_obj.name,
                vertices_count=ungrouped_verts_count
            )
        )

    if has_nonexp_vert_groups:
        raise log.AppError(
            text.error.object_nonexp_group_verts,
            log.props(
                object=bpy_obj.name,
                vertices_count=nonexp_group_verts_count
            )
        )


@log.with_context('armature')
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
        raise log.AppError(
            text.error.object_duplicate_bones,
            log.props(bones=tuple(bone_duplicates.values()))
        )


def merge_meshes(mesh_objects):
    objects = []
    override = bpy.context.copy()
    for obj in mesh_objects:
        if len(obj.data.uv_layers) > 1:
            log.warn(
                text.warn.obj_many_uv,
                exported_uv=obj.data.uv_layers.active.name,
                mesh_object=obj.name
            )
        copy_obj = obj.copy()
        copy_mesh = obj.data.copy()
        copy_obj.data = copy_mesh

        # rename uv layers
        active_uv_name = copy_mesh.uv_layers.active.name
        index = 0
        for uv_layer in copy_mesh.uv_layers:
            if uv_layer.name == active_uv_name:
                continue
            uv_layer.name = str(index)
            index += 1

        copy_mesh.uv_layers.active.name = 'Texture'
        utils.version.link_object(copy_obj)

        # apply modifiers
        override['active_object'] = copy_obj
        override['object'] = copy_obj
        for mod in copy_obj.modifiers:
            if mod.type == 'ARMATURE':
                continue
            if not mod.show_viewport:
                continue
            override['modifier'] = mod
            utils.obj.apply_obj_modifier(mod, context=override)
        objects.append(copy_obj)

        # apply shape keys
        if copy_mesh.shape_keys:
            copy_obj.shape_key_add(name='last_shape_key', from_mix=True)
            for shape_key in copy_mesh.shape_keys.key_blocks:
                copy_obj.shape_key_remove(shape_key)

    active_object = objects[0]
    override['active_object'] = active_object
    override['selected_objects'] = objects
    if utils.version.IS_28:
        override['object'] = active_object
        override['selected_editable_objects'] = objects
    else:
        scene = bpy.context.scene
        override['selected_editable_bases'] = [
            scene.object_bases[ob.name]
            for ob in objects
        ]
    bpy.ops.object.join(override)

    # remove uvs
    uv_layers = [uv_layer.name for uv_layer in active_object.data.uv_layers]
    for uv_name in uv_layers:
        if uv_name == 'Texture':
            continue
        uv_layer = active_object.data.uv_layers[uv_name]
        active_object.data.uv_layers.remove(uv_layer)

    return active_object


def export_meshes(chunked_writer, bpy_root, context, obj_xray):
    armatures = set()
    materials = set()
    meshes = set()
    armature_meshes = set()
    meshes_without_arms = set()
    mesh_writers = []
    uv_maps_names = {}
    merged_obj = None

    loc_space, rot_space, scl_space = utils.ie.get_object_world_matrix(bpy_root)

    def write_mesh(bpy_obj):
        # write mesh chunk
        mesh_writer = rw.write.ChunkedWriter()
        used_material_names = mesh.export_mesh(
            bpy_obj,
            bpy_root,
            mesh_writer,
            context,
            loc_space,
            rot_space,
            scl_space
        )
        mesh_writers.append(mesh_writer)
        meshes.add(bpy_obj)

        # collect materials and uv-map names
        uv_layers = bpy_obj.data.uv_layers

        for material in bpy_obj.data.materials:
            if material:
                if material.name in used_material_names:
                    materials.add(material)
                    uv_maps_names[material.name] = uv_layers.active.name

        if len(uv_layers) > 1:
            log.warn(
                text.warn.obj_many_uv,
                exported_uv=uv_layers.active.name,
                mesh_object=bpy_obj.name
            )

    def scan_root_obj(bpy_obj):
        # scan bone shape helper object
        if utils.obj.is_helper_object(bpy_obj):
            return

        # scan mesh object
        if bpy_obj.type == 'MESH':
            arm_obj = utils.obj.get_armature_object(bpy_obj)
            if arm_obj:
                armature_meshes.add(bpy_obj)
                armatures.add(arm_obj)
            elif armatures:
                armature_meshes.add(bpy_obj)
                meshes_without_arms.add(bpy_obj)
            else:
                write_mesh(bpy_obj)

        # scan children
        for child in bpy_obj.children:
            scan_root_obj(child)

    def search_armatures(bpy_obj):
        if bpy_obj.type == 'ARMATURE':
            armatures.add(bpy_obj)

        for child in bpy_obj.children:
            search_armatures(child)

    search_armatures(bpy_root)
    scan_root_obj(bpy_root)

    # find armature object
    if len(armatures) == 1:
        bpy_arm_obj = list(armatures)[0]

        if meshes_without_arms:
            for obj in meshes_without_arms:
                log.warn(
                    text.warn.obj_used_arm,
                    used_armature=bpy_arm_obj.name,
                    mesh_object=obj.name
                )

    elif len(armatures) > 1:
        raise log.AppError(
            text.error.object_many_arms,
            log.props(
                root_object=bpy_root.name,
                armature_objects=[obj.name for obj in armatures]
            )
        )

    else:
        bpy_arm_obj = None

    # write armature meshes
    if armature_meshes:

        # one mesh
        if len(armature_meshes) == 1:
            mesh_object = list(armature_meshes)[0]
            write_mesh(mesh_object)

        # many meshes
        else:
            merged_obj = merge_meshes(armature_meshes)
            write_mesh(merged_obj)
            mesh_names = [mesh.name for mesh in armature_meshes]
            log.warn(
                text.warn.object_merged,
                objects=mesh_names
            )

    if not mesh_writers:
        raise log.AppError(
            text.error.object_no_meshes,
            log.props(object=bpy_root.name)
        )

    if len(mesh_writers) > 1 and bpy_arm_obj:
        raise log.AppError(
            text.error.object_skel_many_meshes,
            log.props(object=bpy_root.name)
        )

    if bpy_arm_obj:
        for mesh_obj in meshes:
            validate_vertex_weights(mesh_obj, bpy_arm_obj)

    bone_writers = []
    root_bones = []
    if bpy_arm_obj:
        _check_bone_names(bpy_arm_obj)
        bonemap = {}

        arm_mat, scale = utils.ie.get_obj_scale_matrix(bpy_root, bpy_arm_obj)

        utils.ie.check_armature_scale(scale, bpy_root, bpy_arm_obj)

        edit_mode_matrices = {}
        with utils.version.using_active_object(bpy_arm_obj), utils.version.using_mode('EDIT'):
            for edit_bone in bpy_arm_obj.data.edit_bones:
                bone_mat = utils.version.multiply(arm_mat, edit_bone.matrix)
                bone_mat[0][3] *= scale.x
                bone_mat[1][3] *= scale.y
                bone_mat[2][3] *= scale.z
                edit_mode_matrices[edit_bone.name] = bone_mat

        for bpy_bone in bpy_arm_obj.data.bones:
            if not utils.bone.is_exportable_bone(bpy_bone):
                continue
            real_parent = utils.bone.find_bone_exportable_parent(bpy_bone)
            if not real_parent:
                root_bones.append(bpy_bone.name)
            bone.export_bone(
                bpy_arm_obj,
                bpy_bone,
                bone_writers,
                bonemap,
                edit_mode_matrices,
                context.multiply,
                scale
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
            raise log.AppError(
                text.error.object_bad_boneparts,
                log.props(
                    object=bpy_arm_obj.name,
                    bones=invalid_bones
                )
            )

    if len(root_bones) > 1:
        raise log.AppError(
            text.error.object_many_parents,
            log.props(
                object=bpy_arm_obj.name,
                root_bones=root_bones
            )
        )

    export_flags(chunked_writer, obj_xray, bpy_arm_obj)

    meshes_writer = rw.write.ChunkedWriter()
    mesh_index = 0
    for mesh_writer in mesh_writers:
        meshes_writer.put(mesh_index, mesh_writer)
        mesh_index += 1

    chunked_writer.put(fmt.Chunks.Object.MESHES, meshes_writer)

    if merged_obj:
        merged_mesh = merged_obj.data
        if not utils.version.IS_277:
            bpy.data.objects.remove(merged_obj, do_unlink=True)
        else:
            bpy.context.scene.objects.unlink(merged_obj)
            merged_obj.user_clear()
            bpy.data.objects.remove(merged_obj)
        bpy.data.meshes.remove(merged_mesh)

    return materials, bone_writers, bpy_arm_obj, bpy_root, uv_maps_names


def export_surfaces(chunked_writer, context, materials, uv_map_names):
    sfw = rw.write.PackedWriter()
    sfw.putf('<I', len(materials))
    for material in materials:
        sfw.puts(material.name)
        if hasattr(material, 'xray'):
            sfw.puts(material.xray.eshader)
            sfw.puts(material.xray.cshader)
            sfw.puts(material.xray.gamemtl)
        else:
            sfw.puts('')
            sfw.puts('')
            sfw.puts('')
        tex_name = utils.material.get_image_relative_path(
            material,
            context
        )
        sfw.puts(tex_name)
        if utils.version.IS_28:
            sfw.puts(uv_map_names[material.name])
        else:
            slot = material.texture_slots[material.active_texture_index]
            sfw.puts(slot.uv_layer if slot else '')
        if hasattr(material, 'xray'):
            sfw.putf('<I', material.xray.flags)
        else:
            sfw.putf('<I', 0)
        sfw.putf('<I', 0x112)
        sfw.putf('<I', 1)
    chunked_writer.put(fmt.Chunks.Object.SURFACES2, sfw)


def export_bones(chunked_writer, bone_writers):
    if bone_writers:
        writer = rw.write.ChunkedWriter()
        index = 0
        for bone_writer in bone_writers:
            writer.put(index, bone_writer)
            index += 1
        chunked_writer.put(fmt.Chunks.Object.BONES1, writer)


def export_user_data(chunked_writer, xray):
    if xray.userdata:
        user_data = '\r\n'.join(xray.userdata.splitlines())
        packed_writer = rw.write.PackedWriter()
        packed_writer.puts(user_data)
        chunked_writer.put(fmt.Chunks.Object.USERDATA, packed_writer)


def export_lod_ref(chunked_writer, xray):
    if xray.lodref:
        packed_writer = rw.write.PackedWriter()
        packed_writer.puts(xray.lodref)
        chunked_writer.put(fmt.Chunks.Object.LOD_REF, packed_writer)


def export_motions(chunked_writer, some_arm, context, root_obj):
    if some_arm and context.export_motions:
        motions_names = [
            motion.name
            for motion in root_obj.xray.motions_collection
        ]
        motions_names = set(motions_names)
        motions_names = list(motions_names)
        motions_names.sort()
        acts = []
        for act_name in motions_names:
            act = bpy.data.actions.get(act_name, None)
            if act:
                acts.append(act)
            else:
                log.warn(
                    text.warn.object_no_action,
                    action=act_name,
                    object=root_obj.name
                )
        if not acts:
            return
        writer = rw.write.PackedWriter()
        motions.exp.export_motions(writer, acts, some_arm, root_obj)
        if writer.data:
            chunked_writer.put(fmt.Chunks.Object.MOTIONS, writer)


def export_partitions(chunked_writer, some_arm):
    if some_arm and some_arm.pose.bone_groups:
        exportable_bones = tuple(
            bone_
            for bone_ in some_arm.pose.bones
                if utils.bone.is_exportable_bone(
                    some_arm.data.bones[bone_.name]
                )
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
            writer = rw.write.PackedWriter()
            writer.putf('<I', len(non_empty_groups))
            for name, bones in non_empty_groups:
                writer.puts(name)
                writer.putf('<I', len(bones))
                for bone_ in bones:
                    writer.puts(bone_.lower())
            chunked_writer.put(fmt.Chunks.Object.PARTITIONS1, writer)


def export_motion_refs(chunked_writer, xray, context):
    motionrefs = xray.motionrefs_collection
    if motionrefs:
        if xray.motionrefs:
            log.warn(
                text.warn.object_legacy_motionrefs,
                data=xray.motionrefs
            )
        if context.soc_sgroups:
            refs = ','.join(ref.name for ref in motionrefs)
            packed_writer = rw.write.PackedWriter()
            packed_writer.puts(refs)
            chunked_writer.put(fmt.Chunks.Object.MOTION_REFS, packed_writer)
        else:
            writer = rw.write.PackedWriter()
            writer.putf('<I', len(motionrefs))
            for ref in motionrefs:
                writer.puts(ref.name)
            chunked_writer.put(fmt.Chunks.Object.SMOTIONS3, writer)
    elif xray.motionrefs:
        packed_writer = rw.write.PackedWriter()
        packed_writer.puts(xray.motionrefs)
        chunked_writer.put(fmt.Chunks.Object.MOTION_REFS, packed_writer)


def export_transform(chunked_writer, bpy_root):
    root_matrix = bpy_root.matrix_world
    if root_matrix != mathutils.Matrix.Identity(4):
        loc_mat, rot_mat = utils.ie.get_object_transform_matrix(bpy_root)
        writer = rw.write.PackedWriter()
        writer.putv3f(loc_mat.to_translation())
        writer.putv3f(rot_mat.to_euler('YXZ'))
        chunked_writer.put(fmt.Chunks.Object.TRANSFORM, writer)


def export_revision(chunked_writer, xray):
    owner, ctime, moder, mtime = utils.obj.get_revision_data(xray.revision)
    writer = rw.write.PackedWriter()
    writer.puts(owner)
    writer.putf('<I', ctime)
    writer.puts(moder)
    writer.putf('<I', mtime)
    chunked_writer.put(fmt.Chunks.Object.REVISION, writer)


def export_main(bpy_obj, chunked_writer, context):
    xray = bpy_obj.xray

    export_version(chunked_writer)
    export_user_data(chunked_writer, xray)
    export_lod_ref(chunked_writer, xray)
    materials, bone_writers, some_arm, bpy_root, uv_map_names = export_meshes(
        chunked_writer,
        bpy_obj,
        context,
        xray
    )
    export_surfaces(chunked_writer, context, materials, uv_map_names)
    export_bones(chunked_writer, bone_writers)
    export_motions(chunked_writer, some_arm, context, bpy_root)
    export_motion_refs(chunked_writer, xray, context)
    export_partitions(chunked_writer, some_arm)
    export_transform(chunked_writer, bpy_root)
    export_revision(chunked_writer, xray)
