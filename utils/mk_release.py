import os
import zipfile

import utils
import io_scene_xray


def get_zip_file_path():
    vers = io_scene_xray.bl_info['version']
    vers_str = '.'.join(map(str, vers))
    zip_name = 'blender-xray-{}.zip'.format(vers_str)
    zip_path = os.path.join(utils.utils_dir, zip_name)
    return zip_path, zip_name


def get_files_list():
    os.chdir(utils.repo_dir)

    file_list = []

    file_list.append(('LICENSE', 'io_scene_xray/LICENSE'))
    file_list.append('io_scene_xray/ui/stalker.png')

    for root, dirs, files in os.walk('io_scene_xray'):
        for file in files:
            if not file.endswith('.py'):
                continue
            file_path = os.path.join(root, file)
            file_list.append(file_path)

    return file_list


def write_zip_release():
    zip_path, zip_name = get_zip_file_path()
    files = get_files_list()

    with zipfile.ZipFile(zip_path, 'w') as archive:
        for file in files:
            if len(file) == 2:
                input_path, output_path = file
                archive.write(
                    input_path,
                    output_path,
                    compress_type=zipfile.ZIP_DEFLATED
                )
            else:
                archive.write(
                    file,
                    file,
                    compress_type=zipfile.ZIP_DEFLATED
                )

    print('\n\n\tCreated release file: {}'.format(zip_name))
    input('\n\nPress Enter...\n')


write_zip_release()
