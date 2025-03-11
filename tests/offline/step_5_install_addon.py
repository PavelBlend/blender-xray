import os
import shutil
import getpass


user_name = getpass.getuser()
blend_folder = 'C:\\progs\\blender\\'
addons_folder = 'C:\\Users\\{}\\AppData\\Roaming\\Blender Foundation\\Blender\\'.format(user_name)
addon_name = 'io_scene_xray'

addon_src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(os.curdir))), addon_name)

for root, dirs, files in os.walk(blend_folder):
    for file in files:
        if file == 'blender.exe':
            blender_ver = '.'.join(root.split('-')[1].split('.')[0 : 2])
            if not blender_ver[-1].isdigit():
                blender_ver = blender_ver[ : -1]
            addon_folder = os.path.join(addons_folder, blender_ver, 'scripts', 'addons')
            xray_folder = os.path.join(addon_folder, addon_name)
            if os.path.exists(xray_folder):
                shutil.rmtree(xray_folder)
            shutil.copytree(addon_src, xray_folder)
            print('copied:', xray_folder)

input('Press Enter...')
