# blender modules
import bpy

# addon modules
from . import rus


def get_tip(message, message_context='*'):
    return bpy.app.translations.pgettext_tip(message, message_context)


def register():
    translations = {
        'ru_RU': rus.translation,
    }
    bpy.app.translations.register('io_scene_xray', translations)


def unregister():
    bpy.app.translations.unregister('io_scene_xray')
