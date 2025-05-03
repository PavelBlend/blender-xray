# standart modules
import time

# blender modules
import bpy

# addon modules
from .. import fmt
from .... import rw
from .... import utils


def write_revision(obj, ogf_writer):
    revision_writer = rw.write.PackedWriter()

    # get values
    owner, ctime, moder, mtime = utils.obj.get_revis(obj.xray.revision)
    build_time = int(time.time())

    # formatting build name
    prog_name = 'program: blender v{}.{}.{}'.format(*bpy.app.version)
    addon_name = 'addon: blender-xray-v{}.{}.{}'.format(*utils.addon_version)
    build_name = '{}, {}'.format(prog_name, addon_name)

    # formatting source file name
    blend_file = '*.blend file: "{}"'.format(bpy.data.filepath)
    obj_name = 'object: "{}"'.format(obj.name)
    source_file = '{}, {}'.format(blend_file, obj_name)

    # write
    revision_writer.puts(source_file)
    revision_writer.puts(build_name)
    revision_writer.putf('<I', build_time)
    revision_writer.puts(owner)
    revision_writer.putf('<I', ctime)
    revision_writer.puts(moder)
    revision_writer.putf('<I', mtime)

    # write chunk
    ogf_writer.put(fmt.Chunks_v4.S_DESC, revision_writer)


def write_lod(root_obj, ogf_writer):
    lod = root_obj.xray.lodref

    if lod:
        lod_writer = rw.write.PackedWriter()
        lod_writer.puts(lod + '\r\n')
        ogf_writer.put(fmt.Chunks_v4.S_LODS, lod_writer)


def write_userdata(obj, ogf_writer):
    userdata = obj.xray.userdata

    if userdata:
        userdata_writer = rw.write.PackedWriter()
        userdata_writer.puts(userdata)
        ogf_writer.put(fmt.Chunks_v4.S_USERDATA, userdata_writer)
