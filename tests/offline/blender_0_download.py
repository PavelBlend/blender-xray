import os
import urllib.request


# blender version, blender patch version
BLEND_VERS = (
    ('2.77', 'a'),
    ('2.78', 'c'),
    ('2.79', 'b'),
    ('2.80', ''),
    ('2.81', 'a'),
    ('2.82', 'a'),
    ('2.83', '20'),
    ('2.90', '1'),
    ('2.91', '2'),
    ('2.92', '0'),
    ('2.93', '17'),
    ('3.0', '1'),
    ('3.1', '2'),
    ('3.2', '2'),
    ('3.3', '6'),
    ('3.4', '1'),
    ('3.5', '0')
)

download_url = 'https://download.blender.org/release/'
download_folder = 'C:\\progs\\blender\\'

for ver, patch in BLEND_VERS:
    if ver == '2.83' or ver >= '2.93':
        os_name = 'windows-x64'
    else:
        os_name = 'windows64'

    if patch:
        if patch.isdigit():
            full_ver = ver + '.' + patch
        else:
            full_ver = ver + patch

    else:
        full_ver = ver

    file_name = 'blender-{}-{}.zip'.format(full_ver, os_name)
    url = '{}Blender{}/{}'.format(download_url, ver, file_name)
    file_path = os.path.join(download_folder, file_name)

    print('download:', url)
    urllib.request.urlretrieve(url, file_path)

input('Press Enter...')
