# addon modules
from ... import omf
from .... import utils


@utils.stats.timer_stage
def _import_motions(data, context, motions_params, bone_names, ver):
    utils.stats.stage('Motions')
    omf.imp.read_motions(
        data,
        context,
        motions_params,
        bone_names,
        version=ver
    )


def import_skeleton_motions(context, chunks, ogf_chunks, visual):
    motions_data = chunks.pop(ogf_chunks.S_MOTIONS_2, None)
    if motions_data:
        ver = 2
    else:
        motions_data = chunks.pop(ogf_chunks.S_MOTIONS_1, None)
        if motions_data:
            ver = 1
        else:
            motions_data = chunks.pop(ogf_chunks.S_MOTIONS_0, None)
            if motions_data:
                ver = 0
            else:
                ver = None

    params_data = chunks.pop(ogf_chunks.S_SMPARAMS_1, None)
    if params_data:
        param_chunk = 1
    else:
        params_data = chunks.pop(ogf_chunks.S_SMPARAMS_0, None)
        param_chunk = 0

    context.bpy_arm_obj = visual.arm_obj

    if params_data:
        motions_params, bone_names = omf.imp.read_params(
            params_data,
            context,
            param_chunk,
            bones_indices=visual.bones_indices
        )

        if motions_data and context.import_motions:
            _import_motions(
                motions_data,
                context,
                motions_params,
                bone_names,
                ver
            )
