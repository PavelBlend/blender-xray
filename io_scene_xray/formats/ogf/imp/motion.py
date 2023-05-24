# addon modules
from ... import omf


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
        param_ver = 1
    else:
        params_data = chunks.pop(ogf_chunks.S_SMPARAMS_0, None)
        param_ver = 0

    context.bpy_arm_obj = visual.arm_obj

    if params_data:
        motions_params, bone_names = omf.imp.read_params(
            params_data,
            context,
            version=param_ver,
            bones_indices=visual.bones_indices
        )

        if motions_data and context.import_motions:
            omf.imp.read_motions(
                motions_data,
                context,
                motions_params,
                bone_names,
                version=ver
            )

