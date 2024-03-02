# standart modules
import os
import time

# addon modules
from .. import le
from ... import rw
from ... import log
from ... import text
from ... import utils


def _write_object(obj, lines, obj_index, errors):
    loc, rot, scl = le.write.get_transform(obj)
    object_name = le.write.get_obj_name(obj)

    if ' ' in object_name:
        errors.append([obj.name, object_name])
        return

    lines.append('[object_{}]'.format(obj_index))
    lines.append('    clsid = {}'.format(le.fmt.ClassID.OBJECT))
    lines.append('    co_flags = 3')
    lines.append('    flags = 0')
    lines.append('    name = {}'.format(object_name))
    lines.append('    position = {0:.6f}, {0:.6f}, {0:.6f}'.format(*loc))
    lines.append('    reference_name = {}'.format(object_name))
    lines.append('    rotation = {0:.6f}, {0:.6f}, {0:.6f}'.format(*rot))
    lines.append('    scale = {0:.6f}, {0:.6f}, {0:.6f}'.format(*scl))
    lines.append('    version = {}'.format(le.fmt.OBJECT_VER_COP))
    lines.append('')


def _write_objects(lines, objs):
    obj_index = 0
    errors = []

    for obj in objs:
        if obj.xray.isroot:
            _write_object(obj, lines, obj_index, errors)
            obj_index += 1

    if errors:
        if len(errors) == 1:
            obj_name, obj_path = errors[0]
            raise log.AppError(
                text.error.part_no_space,
                log.props(object=obj_name, object_path=obj_path)
            )
        else:
            obj_names = list(map(lambda i: i[0], errors))
            obj_paths = list(map(lambda i: i[1], errors))
            raise log.AppError(
                text.error.part_no_space,
                log.props(
                    objects_count=len(obj_names),
                    objects=obj_names,
                    objects_paths=obj_paths
                )
            )

    if not obj_index:
        raise log.AppError(text.error.object_no_roots)


def _write_modif(lines):
    owner = utils.obj.get_current_user()
    create_time = int(time.time())

    lines.append('[modif]')
    lines.append('    name = {}'.format(owner))
    lines.append('    time = {}'.format(create_time))
    lines.append('')


def _write_main(lines, objs):
    obj_count = le.write.get_obj_count(objs)

    lines.append('[main]')
    lines.append('    flags = 0')
    lines.append('    objects_count = {}'.format(obj_count))
    lines.append('    version = 0')
    lines.append('')


def _write_guid_cop(file_path, lines):
    if os.path.exists(file_path):
        part_ltx = rw.ltx.LtxParser()

        try:
            part_ltx.from_file(file_path)
        except:
            raise log.AppError(
                text.error.part_no_txt,
                log.props(file=file_path)
            )

        guid_data = part_ltx.sections.get('guid', None)

        if guid_data is None:
            raise log.AppError(
                text.error.part_no_guid,
                log.props(file=file_path)
            )

        guid_g0 = guid_data.params.get('guid_g0', None)
        guid_g1 = guid_data.params.get('guid_g1', None)

        if guid_g0 is None or guid_g1 is None:
            raise log.AppError(
                text.error.part_no_guid,
                log.props(file=file_path)
            )

        lines.append('[guid]')
        lines.append('    guid_g0 = {}'.format(guid_g0))
        lines.append('    guid_g1 = {}'.format(guid_g1))
        lines.append('')

    else:
        raise log.AppError(text.error.part_no_file)


def _write_append_random(lines):
    lines.append('[appendrandom]')
    lines.append('    AppendRandomMaxRotation = 0.000000, 0.000000, 0.000000')
    lines.append('    AppendRandomMaxScale = 1.000000, 1.000000, 1.000000')
    lines.append('    AppendRandomMinRotation = 0.000000, 0.000000, 0.000000')
    lines.append('    AppendRandomMinScale = 1.000000, 1.000000, 1.000000')
    lines.append('    AppendRandomObjects_size = 0')
    lines.append('')


def _export_cscop_part(file_path, objs):
    lines = []

    _write_append_random(lines)
    _write_guid_cop(file_path, lines)
    _write_main(lines, objs)
    _write_modif(lines)
    _write_objects(lines, objs)

    return '\n'.join(lines)


def _write_guid_soc(file_path, chunked_writer):
    packed_writer = rw.write.PackedWriter()

    if os.path.exists(file_path):

        with open(file_path, 'rb') as file:
            data = file.read()

        chunked_reader = rw.read.ChunkedReader(data)
        guid_data = chunked_reader.get_chunk(le.fmt.ToolsChunks.GUID)

        if guid_data is None:
            raise log.AppError(
                text.error.part_no_guid,
                log.props(file=file_path)
            )

        packed_writer.data = guid_data

    else:
        raise log.AppError(text.error.part_no_file)

    chunked_writer.put(le.fmt.ToolsChunks.GUID, packed_writer)


def _export_soc_part(file_path, objs, chunked_writer):
    _write_guid_soc(file_path, chunked_writer)
    le.write.write_objects(chunked_writer, objs, part=True)


@log.with_context(name='export-part')
@utils.stats.timer
def export_file(ctx, objs):
    utils.stats.status('Export File', ctx.filepath)
    log.update(file_path=ctx.filepath)

    # shadow of chernobyl
    if ctx.fmt_ver == 'soc':
        writer = rw.write.ChunkedWriter()
        _export_soc_part(ctx.filepath, objs, writer)
        rw.utils.save_file(ctx.filepath, writer)

    # clear sky / call of pripyat
    else:
        file_data = _export_cscop_part(ctx.filepath, objs)

        with open(ctx.filepath, 'w', encoding='cp1251') as file:
            file.write(file_data)
