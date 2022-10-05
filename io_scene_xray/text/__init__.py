# blender modules
import bpy

# addon modules
from . import error
from . import warn
from . import ru


def get_text(message):
    message_context = '*'
    return bpy.app.translations.pgettext_tip(message, message_context)


def register():
    ru.register()


def unregister():
    ru.unregister()
