# addon modules
from .. import fmt
from .... import rw


def write_indices(triangles, two_sided, chunked_writer, verts_count):
    indices_writer = rw.write.PackedWriter()

    indices_count = 3 * len(triangles)
    if two_sided:
        indices_count *= 2
    indices_writer.putf('<I', indices_count)

    for tris in triangles:
        indices_writer.putf('<3H', tris[0], tris[2], tris[1])

    if two_sided:
        offset = verts_count // 2
        for tris in triangles:
            indices_writer.putf(
                '<3H',
                offset + tris[1],
                offset + tris[2],
                offset + tris[0]
            )

    chunked_writer.put(fmt.Chunks_v4.INDICES, indices_writer)
