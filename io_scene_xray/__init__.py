bl_info = {
    'name':     'XRay Engine Tools',
    'author':   'Vakhurin Sergey (igel)',
    'version':  (0, 0, 3),
    'blender':  (2, 7, 0),
    'category': 'Import-Export',
    'location': 'File > Import/Export',
    'description': 'Import/Export X-Ray objects',
    'wiki_url': 'https://github.com/igelbox/blender-xray',
    'tracker_url': 'https://github.com/igelbox/blender-xray/issues',
    'warning':  'Under construction!'
}

try:
    #noinspection PyUnresolvedReferences
    from .plugin import register, unregister
except ImportError:
    pass
