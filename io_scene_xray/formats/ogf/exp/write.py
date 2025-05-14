# addon modules
from . import header
from . import tex
from . import verts
from . import indices
from . import bone
from . import ik
from . import motion
from . import prop
from .. import fmt
from .... import rw


def write_child(obj, writer, ctx, mesh, vertices, triangles, max_wght):

    # header
    header.write_header_child(mesh, writer, max_wght)

    # texture
    two_sided = tex.write_tex(obj, ctx, writer)

    # vertices
    vcount = verts.write_verts(ctx, obj, vertices, two_sided, max_wght, writer)

    # indices
    indices.write_indices(triangles, two_sided, writer, vcount)


def write_children(meshes, ogf_writer):
    children_writer = rw.write.ChunkedWriter()

    for child_index, mesh_writer in enumerate(meshes):
        children_writer.put(child_index, mesh_writer)

    ogf_writer.put(fmt.Chunks_v4.CHILDREN, children_writer)


def write_skeleton(root_obj, arm_obj, ogf_writer, ctx, meshes, bones, scale):

    # header
    header.write_header(root_obj, ogf_writer, ctx, arm_obj)

    # revision
    prop.write_revision(root_obj, ogf_writer)

    # children
    write_children(meshes, ogf_writer)

    # bone names
    bone.write_bone_names(bones, scale, ogf_writer)

    # ik data
    ik.write_ik_data(arm_obj, bones, scale, ogf_writer)

    # user data
    prop.write_userdata(root_obj, ogf_writer)

    # motion references
    motion.write_motion_refs(root_obj, ctx, ogf_writer)

    # motions
    motion.write_motions(root_obj.xray, ctx, arm_obj, ogf_writer)

    # lod
    prop.write_lod(root_obj, ogf_writer)


def write_static(root_obj, ogf_writer, ctx, meshes):

    if len(meshes) == 1:
        mesh_writer = meshes[0]

        # mesh
        ogf_writer.data = mesh_writer.data

    else:
        # header
        header.write_header(root_obj, ogf_writer, ctx, None)

        # children
        write_children(meshes, ogf_writer)

    # revision
    prop.write_revision(root_obj, ogf_writer)

    # user data
    prop.write_userdata(root_obj, ogf_writer)

    # lod
    prop.write_lod(root_obj, ogf_writer)
