bl_info = {
    'name': 'XRay Engine Tools',
    'author': 'Vakhurin Sergey (igel), Pavel_Blend, Viktoria Danchenko',
    'version': (2, 12, 0),
    'blender': (2, 80, 0),
    'category': 'Import-Export',
    'location': 'File > Import/Export',
    'description': 'Import/Export X-Ray objects',
    'wiki_url': 'https://github.com/PavelBlend/blender-xray',
    'doc_url': 'https://github.com/PavelBlend/blender-xray',
    'tracker_url': 'https://github.com/PavelBlend/blender-xray/issues'
}


def register():
    # first import of required blender modules.
    # used in other modules.
    import bpy.utils.previews
    import bpy_extras.io_utils

    # configuring addon modules.
    from . import utils
    from . import xray_io
    xray_io.ENCODE_ERROR = utils.AppError

    # registration
    from . import addon
    addon.register()


def unregister():
    # import of required blender modules.
    # used in other modules.
    import bpy.utils.previews
    import bpy_extras.io_utils

    # unregistration
    from . import addon
    addon.unregister()
