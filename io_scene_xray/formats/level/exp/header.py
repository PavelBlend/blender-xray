# addon modules
from .. import fmt
from .... import rw


def write_header(main_writer):
    header_writer = rw.write.PackedWriter()

    header_writer.putf('<H', fmt.VERSION_14)
    header_writer.putf('<H', 0)    # quality

    main_writer.put(fmt.HEADER, header_writer)
