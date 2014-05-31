import io
import math
import os.path
from .xray_io import ChunkedReader, PackedReader
from .fmt_object import Chunks


class ImportContext:
    def __init__(self, fpath, bpy=None):
        self.file_path = fpath
        self.object_name = os.path.basename(fpath.lower())
        self.bpy = bpy


def warn_imknown_chunk(cid, location):
    print('WARNING: UNKNOWN CHUNK: {:#x} IN: {}'.format(cid, location))


def _import_mesh(cx, cr, parent):
    ver = cr.nextf(Chunks.Mesh.VERSION, 'H')[0]
    if ver != 0x11:
        raise Exception('unsupported MESH format version: {:#x}'.format(ver))
    vertices = []
    faces = []
    for (cid, data) in cr:
        if cid == Chunks.Mesh.VERTS:
            pr = PackedReader(data)
            vc = pr.getf('I')[0]
            vertices = [pr.getf('fff') for _ in range(vc)]
        elif cid == Chunks.Mesh.FACES:
            pr = PackedReader(data)
            fc = pr.getf('I')[0]
            for _ in range(fc):
                fr = pr.getf('IIIIII')
                faces.append((fr[0], fr[2], fr[4]))
    if cx.bpy:
        bpy_mesh = cx.bpy.data.meshes.new('mesh')
        bpy_mesh.from_pydata(vertices, [], faces)

        bpy_obj = cx.bpy.data.objects.new('mobj', bpy_mesh)
        bpy_obj.parent = parent
        cx.bpy.context.scene.objects.link(bpy_obj)
    else:
        print('vertices: ' + str(vertices))
        print('faces: ' + str(faces))


def _import_main(cx, cr):
    ver = cr.nextf(Chunks.Object.VERSION, 'H')[0]
    if ver != 0x10:
        raise Exception('unsupported OBJECT format version: {:#x}'.format(ver))
    if cx.bpy:
        bpy_obj = cx.bpy.data.objects.new(cx.object_name, None)
        bpy_obj.rotation_euler.x = math.pi / 2
        cx.bpy.context.scene.objects.link(bpy_obj)
    else:
        bpy_obj = None
    for (cid, data) in cr:
        if cid == Chunks.Object.MESHES:
            for (_, mdat) in ChunkedReader(data):
                _import_mesh(cx, ChunkedReader(mdat), bpy_obj)
        else:
            warn_imknown_chunk(cid, 'main')


def _import(cx, cr):
    for (cid, data) in cr:
        if cid == Chunks.Object.MAIN:
            _import_main(cx, ChunkedReader(data))
        else:
            warn_imknown_chunk(cid, 'root')


def import_file(cx):
    with io.open(cx.file_path, 'rb') as f:
        _import(cx, ChunkedReader(f.read()))
