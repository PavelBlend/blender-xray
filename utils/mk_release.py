#!/usr/bin/env python3
import utils
from io_scene_xray import bl_info
from zipfile import ZipFile, ZIP_DEFLATED
import os


os.chdir(utils.repo_dir)
zip_name = 'blender-xray-' + ('.'.join(map(str, bl_info['version']))) + '.zip'
zip_path = os.path.join(utils.utils_dir, zip_name)
with ZipFile(zip_path, 'w') as z:
    z.write('LICENSE', 'io_scene_xray/LICENSE', compress_type=ZIP_DEFLATED)
    z.write(
        'io_scene_xray/ui/stalker.png',
        'io_scene_xray/ui/stalker.png',
        compress_type=ZIP_DEFLATED
    )
    for root, _, files in os.walk('io_scene_xray'):
        for file in files:
            if not file.endswith('.py'):
                continue
            z.write(os.path.join(root, file), compress_type=ZIP_DEFLATED)
input('Created release file: {}\n\nPress Enter\n'.format(zip_name))
