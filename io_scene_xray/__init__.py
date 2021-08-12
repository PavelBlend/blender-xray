bl_info = {
    'name': 'XRay Engine Tools',
    'author': 'Vakhurin Sergey (igel), Pavel_Blend, Viktoria Danchenko',
    'version': (1, 10, 0),
    'blender': (2, 80, 0),
    'category': 'Import-Export',
    'location': 'File > Import/Export',
    'description': 'Import/Export X-Ray objects',
    'wiki_url': 'https://github.com/PavelBlend/blender-xray',
    'tracker_url': 'https://github.com/PavelBlend/blender-xray/issues',
    'warning': 'Under construction!'
}


def register():
    from . import addon
    from . import utils
    xray_io.ENCODE_ERROR = utils.AppError
    addon.register()


def unregister():
    from . import addon
    addon.unregister()
