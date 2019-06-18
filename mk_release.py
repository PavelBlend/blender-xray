#!/usr/bin/env python3

from io_scene_xray import bl_info
from zipfile import ZipFile, ZIP_DEFLATED
from os import path, walk

release_file_name = 'blender-xray-' + ('.'.join(map(str, bl_info['version']))) + '.zip'
with ZipFile(release_file_name, 'w') as z:
    z.write('LICENSE', 'io_scene_xray/LICENSE', compress_type=ZIP_DEFLATED)
    z.write(
        'io_scene_xray/icons/stalker.png',
        'io_scene_xray/icons/stalker.png',
        compress_type=ZIP_DEFLATED
    )
    for root, _, files in walk('io_scene_xray'):
        for file in files:
            if not file.endswith('.py'):
                continue
            z.write(path.join(root, file), compress_type=ZIP_DEFLATED)
input('Created release file: {}\n\nPress Enter\n'.format(release_file_name))
