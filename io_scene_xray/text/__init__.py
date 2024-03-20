# blender modules
import bpy

# addon modules
from . import error
from . import warn
from . import ru


MESSAGE_CONTEXT = '*'


def get_tip(message):
    return bpy.app.translations.pgettext_tip(message, MESSAGE_CONTEXT)


def register():
    ru.register()


def unregister():
    ru.unregister()
