# addon modules
from .. import fmt
from .... import text
from .... import log
from .... import rw


def get_version(level, chunks, file):
    data = chunks.pop(fmt.HEADER)
    header_reader = rw.read.PackedReader(data)

    xrlc_version = header_reader.getf('<H')[0]
    if not xrlc_version in fmt.SUPPORTED_VERSIONS:
        raise log.AppError(
            text.error.level_unsupport_ver,
            log.props(
                version=xrlc_version,
                file=file
            )
        )

    if level:
        level.xrlc_version = xrlc_version

    header_reader.skip(2)    # xrlc quality (0 - Draft, 1 - High, 2 - Custom)
