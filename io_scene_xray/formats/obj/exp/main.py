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

        self.body_writer = None
        self.arm_obj = None
        self.materials = None
        self.uv_map_names = None
        self.bone_writers = None

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

    def export_meshes(self):
        ObjectExporterMeshes(self)

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

        # 1 - Dynamic, 3 - Progressive Dynamic
        if self.arm_obj and flags & ~0x40 not in (1, 3):
            # set Dynamic flag so that it is possible
            # to ogf export from ActorEditor
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
            bone_groups = self.get_bone_groups()
            if bone_groups:
                writer = rw.write.PackedWriter()
                groups_count = len(bone_groups)
                writer.putf('<I', groups_count)
                for name, bones in bone_groups:
                    writer.puts(name)
                    bones_count = len(bones)
                    writer.putf('<I', bones_count)
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

            # collect motion names
            motions_names = [
                motion.name
                for motion in self.root_obj.xray.motions_collection
            ]
            motions_names = set(motions_names)
            motions_names = list(motions_names)
            motions_names.sort()

            # collect actions
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

                # create motions context
                motion_ctx = contexts.ExportAnimationOnlyContext()
                motion_ctx.bpy_arm_obj = self.arm_obj

                # export motions
                writer = rw.write.PackedWriter()
                motions.exp.export_motions(
                    writer,
                    acts,
                    motion_ctx,
                    self.root_obj
                )

                # write chunk
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


class ObjectExporterMeshes:

    def __init__(self, body):
        self.body = body

        self.init()
        self.export()

    def init(self):
        self.armatures = set()
        self.meshes = set()
        self.armature_meshes = set()
        self.meshes_without_arms = set()
        self.mesh_writers = []
        self.root_bones = None
        self.edit_mode_matrices = None
        self.merged_obj = None

        self.body.materials = set()
        self.body.uv_map_names = {}

        (
            self.loc_space,
            self.rot_space,
            self.scl_space
        ) = utils.ie.get_object_world_matrix(self.body.root_obj)

    def write_mesh(self, bpy_obj, arm_obj):
        # write mesh chunk
        mesh_writer = rw.write.ChunkedWriter()
        used_material_names = mesh.export_mesh(
            bpy_obj,
            self.body.root_obj,
            arm_obj,
            mesh_writer,
            self.body.context,
            self.loc_space,
            self.rot_space,
            self.scl_space
        )
        self.mesh_writers.append(mesh_writer)
        self.meshes.add(bpy_obj)

        # collect materials and uv-map names
        uv_layers = bpy_obj.data.uv_layers

        for material in bpy_obj.data.materials:
            if material:
                if material.name in used_material_names:
                    self.body.materials.add(material)
                    self.body.uv_map_names[material.name] = uv_layers.active.name

        if len(uv_layers) > 1:
            log.warn(
                text.warn.obj_many_uv,
                exported_uv=uv_layers.active.name,
                mesh_object=bpy_obj.name
            )

    def scan_root_obj(self, exp_objs):
        for bpy_obj in exp_objs:

            # scan bone shape helper object
            if utils.obj.is_helper_object(bpy_obj):
                continue

            # scan mesh object
            if bpy_obj.type == 'MESH':
                arm_obj = utils.obj.get_armature_object(bpy_obj)

                if arm_obj:
                    self.armature_meshes.add(bpy_obj)
                    self.armatures.add(arm_obj)

                elif self.armatures:
                    self.armature_meshes.add(bpy_obj)
                    self.meshes_without_arms.add(bpy_obj)

                else:
                    self.write_mesh(bpy_obj, arm_obj)

    def search_armatures(self, exp_objs):
        for bpy_obj in exp_objs:
            if bpy_obj.type == 'ARMATURE':
                self.armatures.add(bpy_obj)

    def find_arm_obj(self):
        # find armature object

        if len(self.armatures) == 1:
            self.body.arm_obj = list(self.armatures)[0]

            if self.meshes_without_arms:
                for obj in self.meshes_without_arms:
                    log.warn(
                        text.warn.obj_used_arm,
                        used_armature=self.body.arm_obj.name,
                        mesh_object=obj.name
                    )

        elif len(self.armatures) > 1:
            raise log.AppError(
                text.error.object_many_arms,
                log.props(
                    root_object=self.body.root_obj.name,
                    armature_objects=[obj.name for obj in self.armatures]
                )
            )

        else:
            self.body.arm_obj = None

    def write_arm_meshes(self):
        # write armature meshes

        if self.armature_meshes:

            # one mesh
            if len(self.armature_meshes) == 1:
                mesh_object = list(self.armature_meshes)[0]
                utils.ie.validate_vertex_weights(mesh_object, self.body.arm_obj)
                self.write_mesh(mesh_object, self.body.arm_obj)

            # many meshes
            else:
                self.merged_obj = utils.obj.merge_meshes(self.armature_meshes, self.body.arm_obj)
                self.write_mesh(self.merged_obj, self.body.arm_obj)
                mesh_names = [mesh.name for mesh in self.armature_meshes]
                log.warn(
                    text.warn.object_merged,
                    count=str(len(mesh_names)),
                    objects=mesh_names
                )

    def check_mesh_writers(self):
        if not self.mesh_writers:
            utils.obj.remove_merged_obj(self.merged_obj)
            raise log.AppError(
                text.error.object_no_meshes,
                log.props(object=self.body.root_obj.name)
            )

        if len(self.mesh_writers) > 1 and self.body.arm_obj:
            utils.obj.remove_merged_obj(self.merged_obj)
            raise log.AppError(
                text.error.object_skel_many_meshes,
                log.props(object=self.body.root_obj.name)
            )

    def get_bone_edit_mats(self):
        self.edit_mode_matrices = {}

        with utils.version.using_active_object(self.body.arm_obj), utils.version.using_mode('EDIT'):
            for edit_bone in self.body.arm_obj.data.edit_bones:
                bone_mat = edit_bone.matrix
                bone_mat[0][3] *= self.scale.x
                bone_mat[1][3] *= self.scale.y
                bone_mat[2][3] *= self.scale.z
                self.edit_mode_matrices[edit_bone.name] = bone_mat

    def write_bones(self):
        bonemap = {}

        for bpy_bone in self.body.arm_obj.data.bones:

            if not utils.bone.is_exportable_bone(bpy_bone):
                continue

            real_parent = utils.bone.find_bone_exportable_parent(bpy_bone)

            if not real_parent:
                self.root_bones.append(bpy_bone.name)

            bone.export_bone(
                self.body.arm_obj,
                bpy_bone,
                self.body.bone_writers,
                bonemap,
                self.edit_mode_matrices,
                self.body.context.multiply,
                self.scale
            )

    def check_bone_groups(self):
        invalid_bones = []
        has_bone_groups = False

        if len(self.body.arm_obj.pose.bone_groups):
            for bone_ in self.body.arm_obj.pose.bones:
                xray = self.body.arm_obj.data.bones[bone_.name].xray
                if xray.exportable:
                    if bone_.bone_group is None:
                        invalid_bones.append(bone_.name)
                    else:
                        has_bone_groups = True

        if invalid_bones and has_bone_groups:
            utils.obj.remove_merged_obj(self.merged_obj)
            raise log.AppError(
                text.error.object_bad_boneparts,
                log.props(
                    object=self.body.arm_obj.name,
                    bones=invalid_bones
                )
            )

    def check_root_bones(self):
        if len(self.root_bones) > 1:
            utils.obj.remove_merged_obj(self.merged_obj)
            raise log.AppError(
                text.error.object_many_parents,
                log.props(
                    object=self.body.arm_obj.name,
                    root_bones=self.root_bones
                )
            )

    def export_bones(self):
        if self.body.arm_obj:
            self.root_bones = []
            self.body.bone_writers = []

            inspect.bone.check_bone_names(self.body.arm_obj)
            self.scale = self.body.arm_obj.matrix_world.to_scale()
            utils.ie.check_armature_scale(
                self.scale,
                self.body.root_obj,
                self.body.arm_obj
            )
            self.get_bone_edit_mats()
            self.write_bones()
            self.check_bone_groups()
            self.check_root_bones()

    def write_meshes(self):
        meshes_writer = rw.write.ChunkedWriter()

        mesh_index = 0
        for mesh_writer in self.mesh_writers:
            meshes_writer.put(mesh_index, mesh_writer)
            mesh_index += 1

        self.body.body_writer.put(fmt.Chunks.Object.MESHES, meshes_writer)

    def export(self):
        exp_objs = utils.obj.get_exp_objs(self.body.context, self.body.root_obj)

        self.search_armatures(exp_objs)
        self.scan_root_obj(exp_objs)
        self.find_arm_obj()
        self.write_arm_meshes()
        self.check_mesh_writers()
        self.export_bones()
        self.body.export_flags()
        self.write_meshes()

        utils.obj.remove_merged_obj(self.merged_obj)


@log.with_context('export-object')
@utils.stats.timer
def export_file(root_obj, context):
    ObjectExporter(root_obj, context)
