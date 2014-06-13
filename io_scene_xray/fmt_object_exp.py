import bmesh
import bpy
import io
from .xray_io import ChunkedWriter, PackedWriter
from .fmt_object import Chunks


def calculate_bbox(bpy_obj):
    bb = bpy_obj.bound_box
    mn = [bb[0][0], bb[0][1], bb[0][2]]
    mx = [bb[6][0], bb[6][1], bb[6][2]]

    def expand_children_r(cc):
        for c in cc:
            b = c.bound_box
            for i in range(3):
                mn[i] = min(mn[i], b[0][i])
                mx[i] = max(mx[i], b[6][i])
            expand_children_r(c.children)

    expand_children_r(bpy_obj.children)
    for i in range(3):
        mn[i] -= 0.000001
        mx[i] += 0.000001
    return mn, mx


def _export_mesh(bpy_obj, cw):
    cw.put(Chunks.Mesh.VERSION, PackedWriter().putf('H', 0x11))
    cw.put(Chunks.Mesh.MESHNAME, PackedWriter().puts(bpy_obj.name))
    bbox = calculate_bbox(bpy_obj)
    cw.put(Chunks.Mesh.BBOX, PackedWriter().putf('fff', *bbox[0]).putf('fff', *bbox[1]))
    if hasattr(bpy_obj.data, 'xray'):
        cw.put(Chunks.Mesh.FLAGS, PackedWriter().putf('B', bpy_obj.data.xray.flags))
    else:
        cw.put(Chunks.Mesh.FLAGS, PackedWriter().putf('B', 1))

    bm = bmesh.new()
    bm.from_mesh(bpy_obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)

    pw = PackedWriter()
    pw.putf('I', len(bm.verts))
    for v in bm.verts:
        pw.putf('fff', v.co.x, v.co.y, v.co.z)
    cw.put(Chunks.Mesh.VERTS, pw)

    uvs = []
    vtx = []
    fcs = []
    uv_layer = bm.loops.layers.uv.active

    pw = PackedWriter()
    pw.putf('I', len(bm.faces))
    for f in bm.faces:
        for i in range(3):
            pw.putf('II', f.verts[i].index, len(uvs))
            uv = f.loops[i][uv_layer].uv
            uvs.append((uv[0], 1 - uv[1]))
            vtx.append(f.verts[i].index)
            fcs.append(f.index)
    cw.put(Chunks.Mesh.FACES, pw)

    pw = PackedWriter()
    pw.putf('I', len(uvs))
    for i in range(len(uvs)):
        pw.putf('B', 1).putf('II', 0, i)
    cw.put(Chunks.Mesh.VMREFS, pw)

    pw = PackedWriter()
    sfaces = {
        m.name: [fi for fi, f in enumerate(bm.faces) if f.material_index == mi]
        for mi, m in enumerate(bpy_obj.data.materials)
    }
    pw.putf('H', len(sfaces))
    for n, ff in sfaces.items():
        pw.puts(n).putf('I', len(ff))
        for f in ff:
            pw.putf('I', f)
    cw.put(Chunks.Mesh.SFACE, pw)

    def mark_fsg(f, sg):
        ff = [f]
        for f in ff:
            for e in f.edges:
                if not e.smooth:
                    continue
                for lf in e.link_faces:
                    if fsg.get(lf) is None:
                        fsg[lf] = sg
                        ff.append(lf)
    fsg = {}
    sgg = 0
    pw = PackedWriter()
    for f in bm.faces:
        sg = fsg.get(f)
        if sg is None:
            fsg[f] = sg = sgg
            sgg += 1
            mark_fsg(f, sg)
        pw.putf('I', sg)
    cw.put(Chunks.Mesh.SG, pw)

    pw = PackedWriter()
    pw.putf('I', 1)
    at = bpy_obj.data.uv_textures.active
    pw.puts(at.name).putf('B', 2).putf('B', 1).putf('B', 0)
    pw.putf('I', len(uvs))
    for uv in uvs:
        pw.putf('ff', *uv)
    for vi in vtx:
        pw.putf('I', vi)
    for fi in fcs:
        pw.putf('I', fi)
    cw.put(Chunks.Mesh.VMAPS2, pw)


def _export_main(bpy_obj, cw):
    cw.put(Chunks.Object.VERSION, PackedWriter().putf('H', 0x10))
    xr = bpy_obj.xray if hasattr(bpy_obj, 'xray') else None
    cw.put(Chunks.Object.FLAGS, PackedWriter().putf('I', xr.flags if xr is not None else 0))
    msw = ChunkedWriter()
    idx = 0
    for c in bpy_obj.children:
        if c.type != 'MESH':
            continue
        mw = ChunkedWriter()
        _export_mesh(c, mw)
        msw.put(idx, mw)
        idx += 1
    cw.put(Chunks.Object.MESHES, msw)
    materials = [m for m in bpy.data.materials if m.users]
    sfw = PackedWriter()
    sfw.putf('I', len(materials))
    for m in materials:
        sfw.puts(m.name)
        if hasattr(m, 'xray'):
            sfw.puts(m.xray.eshader).puts(m.xray.cshader).puts(m.xray.gamemtl)
        else:
            sfw.puts('').puts('').puts('')
        sfw.puts(m.active_texture.name if m.active_texture else '')
        sfw.puts(m.texture_slots[m.active_texture_index].uv_layer)
        if hasattr(m, 'xray'):
            sfw.putf('I', m.xray.flags)
        else:
            sfw.putf('I', 0)
        sfw.putf('I', 0x112).putf('I', 1)
    cw.put(Chunks.Object.SURFACES2, sfw)


def _export(bpy_obj, cw):
    w = ChunkedWriter()
    _export_main(bpy_obj, w)
    cw.put(Chunks.Object.MAIN, w)


def export_file(bpy_obj, fpath):
    with io.open(fpath, 'wb') as f:
        cw = ChunkedWriter()
        _export(bpy_obj, cw)
        f.write(cw.data)
