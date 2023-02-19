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
        raise log.AppError(
            text.error.object_ungroupped_verts,
            log.props(
                object=bpy_obj.name,
                vertices_count=ungrouped_vertices_count
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
            raise log.AppError(
                text.error.obj_many_uv,
                log.props(object=obj.name)
            )
        copy_obj = obj.copy()
        copy_mesh = obj.data.copy()
        copy_obj.data = copy_mesh
        copy_mesh.uv_layers[0].name = 'Texture'
        utils.version.link_object(copy_obj)
        # apply modifiers
        override['active_object'] = copy_obj
        override['object'] = copy_obj
        for mod in copy_obj.modifiers:
            if mod.type == 'ARMATURE':
                continue
            if not mod.show_viewport:
                continue
            bpy.ops.object.modifier_apply(override, modifier=mod.name)
        objects.append(copy_obj)
    active_object = objects[0]
    override['active_object'] = active_object
    override['selected_objects'] = objects
    if utils.version.IS_28:
        override['object'] = active_object
        override['selected_editable_objects'] = objects
    else:
        scene = bpy.context.scene
        override['selected_editable_bases'] = [scene.object_bases[ob.name] for ob in objects]
    bpy.ops.object.join(override)
    return active_object


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
        mesh_writer = rw.write.ChunkedWriter()
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
                    raise log.AppError(
                        text.error.obj_many_uv,
                        log.props(object=bpy_obj.name)
                    )
                uv_maps_names[material.name] = uv_layers[0].name

    def scan_r(bpy_obj):
        if utils.is_helper_object(bpy_obj):
            return
        if bpy_obj.type == 'MESH':
            arm_obj = utils.get_armature_object(bpy_obj)
            if arm_obj:
                armature_meshes.add(bpy_obj)
                armatures.add(arm_obj)
            else:
                write_mesh(bpy_obj)
        elif bpy_obj.type == 'ARMATURE':
            armatures.add(bpy_obj)
        for child in bpy_obj.children:
            scan_r(child)

    scan_r(bpy_obj)
    if len(armatures) > 1:
        raise log.AppError(
            text.error.object_many_arms,
            log.props(
                root_object=bpy_obj.name,
                armature_objects=[arm_obj.name for arm_obj in armatures]
            )
        )
    if armature_meshes:
        if len(armature_meshes) == 1:
            mesh_object = list(armature_meshes)[0]
            write_mesh(mesh_object)
        else:
            skeletal_obj = merge_meshes(armature_meshes)
            write_mesh(skeletal_obj)
            mesh_names = [mesh.name for mesh in armature_meshes]
            log.warn(
                text.warn.object_merged,
                objects=mesh_names
            )
    if not mesh_writers:
        raise log.AppError(
            text.error.object_no_meshes,
            log.props(object=bpy_obj.name)
        )
    if len(mesh_writers) > 1 and len(armatures):
        raise log.AppError(
            text.error.object_skel_many_meshes,
            log.props(object=bpy_obj.name)
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
        with utils.version.using_active_object(bpy_arm_obj), utils.version.using_mode('EDIT'):
            for bone_ in bpy_arm_obj.data.edit_bones:
                edit_mode_matrices[bone_.name] = bone_.matrix
        for bone_ in bpy_arm_obj.data.bones:
            if not utils.bone.is_exportable_bone(bone_):
                continue
            real_parent = utils.bone.find_bone_exportable_parent(bone_)
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

    arm_list = list(armatures)

    # take care of static objects
    some_arm = arm_list[0] if arm_list else None
    if some_arm:
        if some_arm.scale != mathutils.Vector((1.0, 1.0, 1.0)):
            raise log.AppError(
                text.error.object_bad_scale,
                log.props(
                    object=some_arm.name,
                    scale=tuple(some_arm.scale),
                    scale_must_be=(1.0, 1.0, 1.0)
                )
            )
    export_flags(chunked_writer, obj_xray, some_arm)

    msw = rw.write.ChunkedWriter()
    idx = 0
    for mesh_writer in mesh_writers:
        msw.put(idx, mesh_writer)
        idx += 1

    chunked_writer.put(fmt.Chunks.Object.MESHES, msw)

    if skeletal_obj:
        merged_mesh = skeletal_obj.data
        if not utils.version.IS_277:
            bpy.data.objects.remove(skeletal_obj, do_unlink=True)
        else:
            bpy.context.scene.objects.unlink(skeletal_obj)
            skeletal_obj.user_clear()
            bpy.data.objects.remove(skeletal_obj)
        bpy.data.meshes.remove(merged_mesh)

    return materials, bone_writers, some_arm, bpy_root, uv_maps_names


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
        idx = 0
        for bone_writer in bone_writers:
            writer.put(idx, bone_writer)
            idx += 1
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


def export_motions(chunked_writer, some_arm, context, bpy_obj):
    if some_arm and context.export_motions:
        motions_names = [
            motion.name
            for motion in bpy_obj.xray.motions_collection
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
                    object=bpy_obj.name
                )
        if not acts:
            return
        writer = rw.write.PackedWriter()
        motions.exp.export_motions(writer, acts, some_arm)
        if writer.data:
            chunked_writer.put(fmt.Chunks.Object.MOTIONS, writer)


def export_partitions(chunked_writer, some_arm):
    if some_arm and some_arm.pose.bone_groups:
        exportable_bones = tuple(
            bone_
            for bone_ in some_arm.pose.bones
            if utils.bone.is_exportable_bone(some_arm.data.bones[bone_.name])
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
        writer = rw.write.PackedWriter()
        writer.putv3f(root_matrix.to_translation())
        writer.putv3f(root_matrix.to_euler('YXZ'))
        chunked_writer.put(fmt.Chunks.Object.TRANSFORM, writer)


def export_revision(chunked_writer, xray):
    owner, ctime, moder, mtime = utils.get_revision_data(xray.revision)
    writer = rw.write.PackedWriter()
    writer.puts(owner)
    writer.putf('<I', ctime)
    writer.puts(moder)
    writer.putf('<I', mtime)
    chunked_writer.put(fmt.Chunks.Object.REVISION, writer)


@log.with_context('export-object')
def export_main(bpy_obj, chunked_writer, context):
    log.update(object=bpy_obj.name)
    xray = bpy_obj.xray if hasattr(bpy_obj, 'xray') else None

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
    export_motions(chunked_writer, some_arm, context, bpy_obj)
    export_motion_refs(chunked_writer, xray, context)
    export_partitions(chunked_writer, some_arm)
    export_transform(chunked_writer, bpy_root)
    export_revision(chunked_writer, xray)
