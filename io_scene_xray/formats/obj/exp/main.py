# blender modules
import bpy
import mathutils

# addon modules
from . import mesh
from . import bone
from .. import fmt
from ... import motions
from ... import contexts
from .... import rw
from .... import inspect
from .... import text
from .... import utils
from .... import log


class ObjectExporter:

    def __init__(self, root_obj, context):
        self.root_obj = root_obj
        self.xray = root_obj.xray
        self.context = context

        self.status()
        self.export()

    def export(self):
        self.file_writer = rw.write.ChunkedWriter()
        self.export_body()
        rw.utils.save_file(self.context.filepath, self.file_writer)

    def status(self):
        utils.stats.status('Export File', self.context.filepath)
        log.update(object=self.root_obj.name)

    def export_body(self):
        self.body_writer = rw.write.ChunkedWriter()
        self.export_main()
        self.file_writer.put(fmt.Chunks.Object.MAIN, self.body_writer)

    def export_main(self):
        self.export_version()
        self.export_user_data()
        self.export_lod_ref()
        self.export_meshes()
        self.export_surfaces()
        self.export_bones()
        self.export_motions()
        self.export_motion_refs()
        self.export_partitions()
        self.export_transform()
        self.export_revision()

    def export_version(self):
        packed_writer = rw.write.PackedWriter()
        packed_writer.putf('<H', fmt.CURRENT_OBJECT_VERSION)
        self.body_writer.put(fmt.Chunks.Object.VERSION, packed_writer)

    def export_flags(self):
        flags = self.get_flags()

        packed_writer = rw.write.PackedWriter()
        packed_writer.putf('<I', flags)
        self.body_writer.put(fmt.Chunks.Object.FLAGS, packed_writer)

    def get_flags(self):
        flags = self.xray.flags

        if self.arm_obj:
            # 1 - Dynamic
            # 3 - Progressive Dynamic
            if flags & ~0x40 not in (1, 3):
                # set Dynamic flag
                # so that it is possible to export to ogf from ActorEditor
                flags = 1 | (flags & 0x40)
                log.warn(
                    text.warn.object_set_dynamic,
                    object=self.xray.id_data.name,
                    has_type=fmt.type_names[self.xray.flags_simple],
                    save_as=fmt.type_names[fmt.DY]
                )

        return flags

    def export_user_data(self):
        userdata = self.xray.userdata
        if userdata:
            user_data = '\r\n'.join(userdata.splitlines())
            packed_writer = rw.write.PackedWriter()
            packed_writer.puts(user_data)
            self.body_writer.put(fmt.Chunks.Object.USERDATA, packed_writer)

    def export_lod_ref(self):
        lod_ref = self.xray.lodref
        if lod_ref:
            packed_writer = rw.write.PackedWriter()
            packed_writer.puts(lod_ref)
            self.body_writer.put(fmt.Chunks.Object.LOD_REF, packed_writer)

    def export_revision(self):
        owner, ctime, moder, mtime = utils.obj.get_revis(self.xray.revision)
        writer = rw.write.PackedWriter()
        writer.puts(owner)
        writer.putf('<I', ctime)
        writer.puts(moder)
        writer.putf('<I', mtime)
        self.body_writer.put(fmt.Chunks.Object.REVISION, writer)

    def export_transform(self):
        root_matrix = self.root_obj.matrix_world
        if root_matrix != mathutils.Matrix.Identity(4):
            loc_mat, rot_mat = utils.ie.get_object_transform_matrix(self.root_obj)
            writer = rw.write.PackedWriter()
            writer.putv3f(loc_mat.to_translation())
            writer.putv3f(rot_mat.to_euler('YXZ'))
            self.body_writer.put(fmt.Chunks.Object.TRANSFORM, writer)

    def export_motion_refs(self):
        motionrefs = self.xray.motionrefs_collection
        legacy_refs = self.xray.motionrefs

        # export motion references from collection
        if motionrefs:
            # legacy warning
            if legacy_refs:
                log.warn(
                    text.warn.object_legacy_motionrefs,
                    data=legacy_refs
                )
            # soc format
            if self.context.soc_sgroups:
                refs = ','.join(ref.name for ref in motionrefs)
                self.export_motion_refs_soc(refs)
            # cs/cop format
            else:
                refs = [ref.name for ref in motionrefs]
                self.export_motion_refs_cscop(refs)

        # export legacy motion references
        elif legacy_refs:
            # soc format
            if self.context.soc_sgroups:
                self.export_motion_refs_soc(legacy_refs)
            # cs/cop format
            else:
                refs = legacy_refs.split(',')
                self.export_motion_refs_cscop(refs)

    def export_motion_refs_soc(self, refs):
        writer = rw.write.PackedWriter()
        writer.puts(refs)
        self.body_writer.put(fmt.Chunks.Object.MOTION_REFS, writer)

    def export_motion_refs_cscop(self, refs):
        writer = rw.write.PackedWriter()
        refs_count = len(refs)
        writer.putf('<I', refs_count)
        for ref in refs:
            writer.puts(ref)
        self.body_writer.put(fmt.Chunks.Object.SMOTIONS3, writer)

    def export_partitions(self):
        if self.arm_obj and self.arm_obj.pose.bone_groups:
            non_empty_groups = self.get_bone_groups()
            if non_empty_groups:
                writer = rw.write.PackedWriter()
                writer.putf('<I', len(non_empty_groups))
                for name, bones in non_empty_groups:
                    writer.puts(name)
                    writer.putf('<I', len(bones))
                    for bone_name in bones:
                        writer.puts(bone_name.lower())
                self.body_writer.put(fmt.Chunks.Object.PARTITIONS1, writer)

    def get_bone_groups(self):
        exportable_bones = tuple(
            pose_bone
            for pose_bone in self.arm_obj.pose.bones
                if utils.bone.is_exportable_bone(
                    self.arm_obj.data.bones[pose_bone.name]
                )
        )

        all_groups = (
            (group.name, tuple(
                pose_bone.name
                for pose_bone in exportable_bones
                    if pose_bone.bone_group == group
            ))
            for group in self.arm_obj.pose.bone_groups
        )

        non_empty_groups = tuple(
            group
            for group in all_groups
                if group[1]
        )

        return non_empty_groups

    def export_motions(self):
        if self.arm_obj and self.context.export_motions:
            motions_names = [
                motion.name
                for motion in self.root_obj.xray.motions_collection
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
                        object=self.root_obj.name
                    )
            if acts:
                writer = rw.write.PackedWriter()
                motion_ctx = contexts.ExportAnimationOnlyContext()
                motion_ctx.bpy_arm_obj = self.arm_obj
                motions.exp.export_motions(writer, acts, motion_ctx, self.root_obj)
                if writer.data:
                    self.body_writer.put(fmt.Chunks.Object.MOTIONS, writer)

    def export_bones(self):
        if self.bone_writers:
            writer = rw.write.ChunkedWriter()

            for bone_index, bone_writer in enumerate(self.bone_writers):
                writer.put(bone_index, bone_writer)

            self.body_writer.put(fmt.Chunks.Object.BONES1, writer)

    def export_surfaces(self):
        writer = rw.write.PackedWriter()

        surface_count = len(self.materials)
        writer.putf('<I', surface_count)

        for material in self.materials:
            tex_name = utils.material.get_image_relative_path(material, self.context)

            if utils.version.IS_28:
                uv_name = self.uv_map_names[material.name]
            else:
                slot = material.texture_slots[material.active_texture_index]
                uv_name = slot.uv_layer if slot else ''

            # write
            writer.puts(material.name)
            writer.puts(material.xray.eshader)
            writer.puts(material.xray.cshader)
            writer.puts(material.xray.gamemtl)
            writer.puts(tex_name)
            writer.puts(uv_name)
            writer.putf('<I', material.xray.flags)
            writer.putf('<I', fmt.VERTEX_FORMAT)
            writer.putf('<I', fmt.UV_COUNT)

        self.body_writer.put(fmt.Chunks.Object.SURFACES2, writer)

    def export_meshes(self):
        armatures = set()
        self.materials = set()
        meshes = set()
        armature_meshes = set()
        meshes_without_arms = set()
        mesh_writers = []
        self.uv_map_names = {}
        merged_obj = None

        loc_space, rot_space, scl_space = utils.ie.get_object_world_matrix(self.root_obj)

        def write_mesh(bpy_obj, arm_obj):
            # write mesh chunk
            mesh_writer = rw.write.ChunkedWriter()
            used_material_names = mesh.export_mesh(
                bpy_obj,
                self.root_obj,
                arm_obj,
                mesh_writer,
                self.context,
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
                        self.materials.add(material)
                        self.uv_map_names[material.name] = uv_layers.active.name

            if len(uv_layers) > 1:
                log.warn(
                    text.warn.obj_many_uv,
                    exported_uv=uv_layers.active.name,
                    mesh_object=bpy_obj.name
                )

        def scan_root_obj(exp_objs):
            for bpy_obj in exp_objs:

                # scan bone shape helper object
                if utils.obj.is_helper_object(bpy_obj):
                    continue

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
                        write_mesh(bpy_obj, arm_obj)

        def search_armatures(exp_objs):
            for bpy_obj in exp_objs:
                if bpy_obj.type == 'ARMATURE':
                    armatures.add(bpy_obj)

        exp_objs = utils.obj.get_exp_objs(self.context, self.root_obj)

        search_armatures(exp_objs)
        scan_root_obj(exp_objs)

        # find armature object
        if len(armatures) == 1:
            self.arm_obj = list(armatures)[0]

            if meshes_without_arms:
                for obj in meshes_without_arms:
                    log.warn(
                        text.warn.obj_used_arm,
                        used_armature=self.arm_obj.name,
                        mesh_object=obj.name
                    )

        elif len(armatures) > 1:
            raise log.AppError(
                text.error.object_many_arms,
                log.props(
                    root_object=self.root_obj.name,
                    armature_objects=[obj.name for obj in armatures]
                )
            )

        else:
            self.arm_obj = None

        # write armature meshes
        if armature_meshes:

            # one mesh
            if len(armature_meshes) == 1:
                mesh_object = list(armature_meshes)[0]
                utils.ie.validate_vertex_weights(mesh_object, self.arm_obj)
                write_mesh(mesh_object, self.arm_obj)

            # many meshes
            else:
                merged_obj = utils.obj.merge_meshes(armature_meshes, self.arm_obj)
                write_mesh(merged_obj, self.arm_obj)
                mesh_names = [mesh.name for mesh in armature_meshes]
                log.warn(
                    text.warn.object_merged,
                    count=str(len(mesh_names)),
                    objects=mesh_names
                )

        if not mesh_writers:
            utils.obj.remove_merged_obj(merged_obj)
            raise log.AppError(
                text.error.object_no_meshes,
                log.props(object=self.root_obj.name)
            )

        if len(mesh_writers) > 1 and self.arm_obj:
            utils.obj.remove_merged_obj(merged_obj)
            raise log.AppError(
                text.error.object_skel_many_meshes,
                log.props(object=self.root_obj.name)
            )

        self.bone_writers = []
        root_bones = []
        if self.arm_obj:
            inspect.bone.check_bone_names(self.arm_obj)
            bonemap = {}

            arm_mat, scale = utils.ie.get_obj_scale_matrix(self.root_obj, self.arm_obj)

            utils.ie.check_armature_scale(scale, self.root_obj, self.arm_obj)

            edit_mode_matrices = {}
            with utils.version.using_active_object(self.arm_obj), utils.version.using_mode('EDIT'):
                for edit_bone in self.arm_obj.data.edit_bones:
                    bone_mat = utils.version.multiply(arm_mat, edit_bone.matrix)
                    bone_mat[0][3] *= scale.x
                    bone_mat[1][3] *= scale.y
                    bone_mat[2][3] *= scale.z
                    edit_mode_matrices[edit_bone.name] = bone_mat

            for bpy_bone in self.arm_obj.data.bones:
                if not utils.bone.is_exportable_bone(bpy_bone):
                    continue
                real_parent = utils.bone.find_bone_exportable_parent(bpy_bone)
                if not real_parent:
                    root_bones.append(bpy_bone.name)
                bone.export_bone(
                    self.arm_obj,
                    bpy_bone,
                    self.bone_writers,
                    bonemap,
                    edit_mode_matrices,
                    self.context.multiply,
                    scale
                )

            invalid_bones = []
            has_bone_groups = False
            if len(self.arm_obj.pose.bone_groups):
                for bone_ in self.arm_obj.pose.bones:
                    xray = self.arm_obj.data.bones[bone_.name].xray
                    if xray.exportable:
                        if bone_.bone_group is None:
                            invalid_bones.append(bone_.name)
                        else:
                            has_bone_groups = True
            if invalid_bones and has_bone_groups:
                utils.obj.remove_merged_obj(merged_obj)
                raise log.AppError(
                    text.error.object_bad_boneparts,
                    log.props(
                        object=self.arm_obj.name,
                        bones=invalid_bones
                    )
                )

        if len(root_bones) > 1:
            utils.obj.remove_merged_obj(merged_obj)
            raise log.AppError(
                text.error.object_many_parents,
                log.props(
                    object=self.arm_obj.name,
                    root_bones=root_bones
                )
            )

        self.export_flags()

        meshes_writer = rw.write.ChunkedWriter()
        mesh_index = 0
        for mesh_writer in mesh_writers:
            meshes_writer.put(mesh_index, mesh_writer)
            mesh_index += 1

        self.body_writer.put(fmt.Chunks.Object.MESHES, meshes_writer)

        utils.obj.remove_merged_obj(merged_obj)


@log.with_context('export-object')
@utils.stats.timer
def export_file(root_obj, context):
    ObjectExporter(root_obj, context)
