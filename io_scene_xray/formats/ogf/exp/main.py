# addon modules
from . import arm
from . import mesh
from . import write
from .... import inspect
from .... import rw
from .... import log
from .... import utils


def _scan_obj(bpy_obj, root_obj, meshes, arms, bones, bones_map, ctx):
    if utils.obj.is_helper_object(bpy_obj):
        return

    # scan mesh
    if bpy_obj.type == 'MESH':
        mesh.scan_mesh(ctx, bpy_obj, root_obj, meshes, bones, bones_map)

    # scan armature
    elif bpy_obj.type == 'ARMATURE':
        arm.scan_arm(bpy_obj, arms, bones, bones_map)


def _export_main(root_obj, writer, ctx):

    meshes = []
    arms = []
    bones = []
    bones_map = {}

    exp_objs = utils.obj.get_exp_objs(ctx, root_obj)
    for obj in exp_objs:
        _scan_obj(obj, root_obj, meshes, arms, bones, bones_map, ctx)

    # get armature
    arm_obj = arm.get_arm(root_obj, arms)

    if arm_obj:

        # check bone names
        inspect.bone.check_bone_names(arm_obj)

        # get armature scale
        scale = arm.get_arm_scale(root_obj, arm_obj)

        # write skeleton
        write.write_skeleton(
            root_obj,
            arm_obj,
            writer,
            ctx,
            meshes,
            bones,
            scale
        )

    else:

        # write static
        write.write_static(
            root_obj,
            writer,
            ctx,
            meshes
        )


@log.with_context('export-ogf')
@utils.stats.timer
def export_file(bpy_obj, file_path, ctx):
    utils.stats.status('Export File', file_path)
    log.update(object=bpy_obj.name)

    ogf_writer = rw.write.ChunkedWriter()
    _export_main(bpy_obj, ogf_writer, ctx)
    rw.utils.save_file(file_path, ogf_writer)
