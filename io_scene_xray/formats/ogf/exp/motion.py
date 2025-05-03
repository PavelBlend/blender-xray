# addon modules
from .. import fmt
from ... import omf
from .... import rw


def _get_motion_context(context, arm_obj):
    motion_context = omf.ops.ExportOmfContext()

    motion_context.bpy_arm_obj = arm_obj
    motion_context.export_mode = 'OVERWRITE'
    motion_context.export_motions = True
    motion_context.export_bone_parts = True
    motion_context.need_motions = True
    motion_context.need_bone_groups = True

    if context.fmt_ver == 'soc':
        motion_context.params_ver = 3
        motion_context.high_quality = False
    else:
        motion_context.params_ver = 4
        motion_context.high_quality = context.hq_export

    return motion_context


def write_motions(xray, context, arm_obj, ogf_writer):
    if context.export_motions and xray.motions_collection:
        motion_context = _get_motion_context(context, arm_obj)
        motions_writer = omf.exp.export_omf(motion_context)
        # append motions chunks
        ogf_writer.data.extend(motions_writer.data)


def write_motion_refs(obj, context, ogf_writer):
    refs_collect = obj.xray.motionrefs_collection

    if len(refs_collect):
        refs_writer = rw.write.PackedWriter()
        refs = [ref.name for ref in refs_collect]

        # soc format
        if context.fmt_ver == 'soc':
            refs_string = ','.join(refs)
            refs_writer.puts(refs_string)
            chunk_id = fmt.Chunks_v4.S_MOTION_REFS_0

        # cs/cop format
        else:
            refs_count = len(refs)
            refs_writer.putf('<I', refs_count)
            for ref in refs:
                refs_writer.puts(ref)
            chunk_id = fmt.Chunks_v4.S_MOTION_REFS_2

        ogf_writer.put(chunk_id, refs_writer)
