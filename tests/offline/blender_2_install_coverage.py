import os
import shutil
import tarfile
import urllib.request


cov_url = 'https://files.pythonhosted.org/packages/38/df/d5e67851e83948def768d7fb1a0fd373665b20f56ff63ed220c6cd16cb11/coverage-5.5.tar.gz'
blend_folder = 'C:\\progs\\blender\\'
cov_name = 'coverage-5.5.tar.gz'

print('download:')
print(cov_name)
print()

cov_path = os.path.join(blend_folder, cov_name)
urllib.request.urlretrieve(cov_url, cov_path)

tar_path = os.path.join(blend_folder, cov_name)
tar_unpack = os.path.join(blend_folder, 'coverage_unzip')
cov_module_path = os.path.join(tar_unpack, 'coverage-5.5', 'coverage')

print('extract:')
print(tar_path)
print(tar_unpack)
print()

tar = tarfile.open(tar_path , 'r:gz')
tar.extractall(tar_unpack)
tar.close()

for root, dirs, files in os.walk(blend_folder):
    for directory in dirs:
        if directory == 'site-packages':
            dir_path = os.path.join(root, directory, 'coverage')
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
            print('copy coverage:')
            print(dir_path)
            print()
            shutil.copytree(cov_module_path, dir_path)

input('Press Enter...')
