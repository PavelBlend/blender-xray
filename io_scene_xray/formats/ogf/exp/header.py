# addon modules
from .. import fmt
from .... import rw
from .... import utils


FIRST_SHADER = 0


def _get_model_type(xray, context, arm):
    if arm:
        if len(xray.motionrefs_collection):
            model_type = fmt.ModelType_v4.SKELETON_ANIM

        elif len(xray.motions_collection) and context.export_motions:
            model_type = fmt.ModelType_v4.SKELETON_ANIM

        else:
            model_type = fmt.ModelType_v4.SKELETON_RIGID

    else:
        model_type = fmt.ModelType_v4.HIERRARHY

    return model_type


def _write_header_bounds(obj, header_writer):
    # get bounds
    (b_min, b_max), (cntr, rad) = utils.mesh.calculate_bbox_and_bsphere(obj)

    # bbox
    header_writer.putv3f(b_min)    # min bbox
    header_writer.putv3f(b_max)    # max bbox

    # bsphere
    header_writer.putv3f(cntr)    # bsphere center
    header_writer.putf('<f', rad)    # bsphere radius


def _write_header_base(obj, header_writer, context, arm):
    model_type = _get_model_type(obj.xray, context, arm)
    header_writer.putf('<2BH', fmt.FORMAT_VERSION_4, model_type, FIRST_SHADER)


def write_header_child(mesh, chunked_writer, max_weights):
    # calculate bbox and bsphere
    bbox_min, bbox_max = utils.mesh.calculate_mesh_bbox(mesh.verts)
    bsph_ctr, bsph_rad = utils.mesh.calculate_mesh_bsphere(
        (bbox_min, bbox_max),
        mesh.verts
    )

    # create writer
    header_writer = rw.write.PackedWriter()

    # get model type
    if max_weights:
        model_type = fmt.ModelType_v4.SKELETON_GEOMDEF_ST
    else:
        model_type = fmt.ModelType_v4.NORMAL

    # write
    header_writer.putf('<B', fmt.FORMAT_VERSION_4)
    header_writer.putf('<B', model_type)
    header_writer.putf('<H', FIRST_SHADER)
    header_writer.putv3f(bbox_min)
    header_writer.putv3f(bbox_max)
    header_writer.putv3f(bsph_ctr)
    header_writer.putf('<f', bsph_rad)

    # write chunk
    chunked_writer.put(fmt.HEADER, header_writer)


def write_header(root_obj, ogf_writer, context, arm):
    header_writer = rw.write.PackedWriter()

    _write_header_base(root_obj, header_writer, context, arm)
    _write_header_bounds(root_obj, header_writer)

    ogf_writer.put(fmt.HEADER, header_writer)
