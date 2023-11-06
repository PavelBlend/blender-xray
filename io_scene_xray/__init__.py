bl_info = {
    'name': 'XRay Engine Tools',
    'author': 'Vakhurin Sergey (igel), Pavel_Blend, Viktoria Danchenko',
    'version': (2, 32, 6),
    'blender': (2, 80, 0),
    'category': 'Import-Export',
    'location': 'File > Import/Export',
    'support': 'COMMUNITY',
    'description': 'Import/Export X-Ray Engine files (S.T.A.L.K.E.R. Game).',
    'wiki_url': 'https://github.com/PavelBlend/blender-xray',
    'doc_url': 'https://github.com/PavelBlend/blender-xray',
    'tracker_url': 'https://github.com/PavelBlend/blender-xray/issues'
}


def register():
    # first import of required blender modules.
    # used in other modules.
    import bpy.utils.previews
    import bpy_extras.io_utils

    # registration
    from . import addon
    addon.register()

    # configuring addon modules.
    from . import utils
    utils.addon_version = bl_info['version']


def unregister():
    # import of required blender modules.
    # used in other modules.
    import bpy.utils.previews
    import bpy_extras.io_utils

    # unregistration
    from . import addon
    addon.unregister()
