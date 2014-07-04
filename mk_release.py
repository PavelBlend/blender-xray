#!/usr/bin/env python3

from io_scene_xray import bl_info
from zipfile import ZipFile, ZIP_DEFLATED
from os import path, walk

with ZipFile('blender-xray-' + ('.'.join(map(str, bl_info['version']))) + '.zip', 'w') as z:
    z.write('LICENSE', 'io_scene_xray/LICENSE', compress_type=ZIP_DEFLATED)
    for root, _, files in walk('io_scene_xray'):
        for file in files:
            if not file.endswith('.py'):
                continue
            z.write(path.join(root, file), compress_type=ZIP_DEFLATED)
