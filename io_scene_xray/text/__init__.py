# blender modules
import bpy

# addon modules
from . import error
from . import warn
from . import ru


def get_text(message):
    message_context = '*'
    translate = bpy.app.translations.pgettext_tip(message, message_context)
    translate = translate.strip()
    translate = translate[0].upper() + translate[1: ]
    return translate


def register():
    ru.register()


def unregister():
    ru.unregister()
