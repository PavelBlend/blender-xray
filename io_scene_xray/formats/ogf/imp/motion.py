# addon modules
from ... import omf


def import_skeleton_motions(context, chunks, ogf_chunks, visual):
    motions_data = chunks.pop(ogf_chunks.S_MOTIONS, None)
    params_data = chunks.pop(ogf_chunks.S_SMPARAMS, None)

    context.bpy_arm_obj = visual.arm_obj

    if params_data:
        motions_params, bone_names = omf.imp.read_params(params_data, context)

        if motions_data and context.import_motions:
            omf.imp.read_motions(
                motions_data,
                context,
                motions_params,
                bone_names
            )

