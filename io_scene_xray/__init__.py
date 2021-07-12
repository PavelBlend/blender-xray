bl_info = {
    'name': 'XRay Engine Tools',
    'author': 'Vakhurin Sergey (igel), Pavel_Blend, Viktoria Danchenko',
    'version': (1, 8, 3),
    'blender': (2, 80, 0),
    'category': 'Import-Export',
    'location': 'File > Import/Export',
    'description': 'Import/Export X-Ray objects',
    'wiki_url': 'https://github.com/PavelBlend/blender-xray',
    'tracker_url': 'https://github.com/PavelBlend/blender-xray/issues',
    'warning': 'Under construction!'
}


def register():
    from . import registry, plugin, xray_inject_ui
    plugin.register()
    registry.register_thing(xray_inject_ui, __name__)


def unregister():
    from . import registry, plugin, xray_inject_ui
    registry.unregister_thing(xray_inject_ui, __name__)
    plugin.unregister()
