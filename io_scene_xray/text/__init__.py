# addon modules
from . import error
from . import warn
from .. import translate


def get_text(*strings, data=()):
    strings_list = []
    for index, string in enumerate(strings):
        if index in data:
            string = '"{}"'.format(string)
        else:
            string = translate.get_tip(string)
        strings_list.append(string)
    message_text = ' '.join(strings_list) + '.'
    first_char = message_text[0].upper()
    result = first_char + message_text[1 : ]
    return result
