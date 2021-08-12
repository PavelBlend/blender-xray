# blender modules
import bpy

# addon modules
from . import ops
from . import ui
from . import plugin_prefs
from . import edit_helpers
from . import hotkeys
from . import props
from . import skls_browser
from . import icons
from . import utils
from . import version_utils
from . import xray_io

# plugin modules
from . import details
from . import dm
from . import err
from . import scene
from . import obj
from . import anm
from . import skl
from . import bones
from . import ogf
from . import level
from . import omf


xray_io.ENCODE_ERROR = utils.AppError


def overlay_view_3d():
    def try_draw(base_obj, obj):
        if not hasattr(obj, 'xray'):
            return
        xray = obj.xray
        if hasattr(xray, 'ondraw_postview'):
            xray.ondraw_postview(base_obj, obj)
        if hasattr(obj, 'type'):
            if obj.type == 'ARMATURE':
                for bone in obj.data.bones:
                    try_draw(base_obj, bone)

    for obj in bpy.data.objects:
        try_draw(obj, obj)


_INITIALIZER = utils.ObjectsInitializer([
    'objects',
    'materials',
])


@bpy.app.handlers.persistent
def load_post(_):
    _INITIALIZER.sync('LOADED', bpy.data)


@bpy.app.handlers.persistent
def scene_update_post(_):
    _INITIALIZER.sync('CREATED', bpy.data)


def register():
    icons.register()
    details.register()
    skls_browser.register()
    props.register()
    plugin_prefs.register()

    obj.imp.ops.register()
    obj.exp.ops.register()
    anm.ops.register()
    dm.ops.register()
    bones.ops.register()
    ogf.ops.register()
    skl.ops.register()
    omf.ops.register()
    scene.ops.register()
    level.ops.register()
    err.ops.register()
    overlay_view_3d.__handle = bpy.types.SpaceView3D.draw_handler_add(
        overlay_view_3d, (),
        'WINDOW', 'POST_VIEW'
    )
    bpy.app.handlers.load_post.append(load_post)
    version_utils.get_scene_update_post().append(scene_update_post)
    hotkeys.register()
    edit_helpers.register()
    ops.register()
    ui.register()


def unregister():
    ui.unregister()
    ops.unregister()
    edit_helpers.unregister()
    hotkeys.unregister()
    err.ops.unregister()
    dm.ops.unregister()
    bones.ops.unregister()
    ogf.ops.unregister()
    level.ops.unregister()
    scene.ops.unregister()
    omf.ops.unregister()
    skl.ops.unregister()
    anm.ops.unregister()
    obj.exp.ops.unregister()
    obj.imp.ops.unregister()

    version_utils.get_scene_update_post().remove(scene_update_post)
    bpy.app.handlers.load_post.remove(load_post)
    bpy.types.SpaceView3D.draw_handler_remove(overlay_view_3d.__handle, 'WINDOW')

    plugin_prefs.unregister()
    props.unregister()
    skls_browser.unregister()
    details.unregister()
    icons.unregister()
