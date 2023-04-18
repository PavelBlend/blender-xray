import os
import zipfile


blender_folder = 'C:\\progs\\blender\\'

for file in os.listdir(blender_folder):
    path = os.path.join(blender_folder, file)

    if not os.path.isfile(path):
        continue

    if not path.endswith('.zip'):
        continue

    print('unzip:')
    print(path)
    print()

    with zipfile.ZipFile(path, 'r') as zip_file:
        zip_file.extractall(blender_folder)

input('Press Enter...')
