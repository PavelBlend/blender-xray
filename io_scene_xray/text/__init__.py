# addon modules
from . import error
from . import warn
from .. import translate


def get_text(string):
    result = translate.get_tip(string)
    return result
