
def load_mesh(cx, pr, dm, PackedReader):

    from io_scene_xray.utils import AppError

    if dm.mesh.indices_count % 3 != 0:
        raise AppError('bad dm triangle indices')

    import bmesh

    bm = bmesh.new()

    S_FFFFF = PackedReader.prep('fffff')    

    uvs = {}

    for _ in range(dm.mesh.vertices_count):
        v = pr.getp(S_FFFFF)    # x, y, z, u, v
        bm_vert = bm.verts.new((v[0], v[2], v[1]))
        uvs[bm_vert] = (v[3], v[4])

    bm.verts.ensure_lookup_table()
    S_HHH = PackedReader.prep('HHH')

    for _ in range(dm.mesh.indices_count // 3):

        fi = pr.getp(S_HHH)    # face indices

        try:
            bm.faces.new(
                (bm.verts[fi[0]], bm.verts[fi[2]], bm.verts[fi[1]])
                ).smooth = True
        except ValueError:
            pass

    bm.faces.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.new(dm.mesh.uv_map_name)

    if dm.mode == 'DM':
        for face in bm.faces:
            for loop in face.loops:
                loop[uv_layer].uv = uvs[loop.vert]

    elif dm.mode == 'DETAILS':
        for face in bm.faces:
            for loop in face.loops:
                uv = uvs[loop.vert]
                loop[uv_layer].uv = uv[0], 1 - uv[1]

    else:
        raise Exception(
            'unknown dm import mode: {0}. ' \
            'You must use DM or DETAILS'.format(dm.mode)
            )

    bml_tex = bm.faces.layers.tex.new(dm.mesh.uv_map_name)
    bpy_image = dm.mesh.bpy_material.texture_slots[0].texture.image

    for bmf in bm.faces:
        bmf[bml_tex].image = bpy_image

    bm.normal_update()
    bm.to_mesh(dm.mesh.bpy_mesh)
