import os
import pylint.lint


addon_folder = 'io_scene_xray'
if os.path.exists(addon_folder):
    pylint_path = addon_folder
else:
    current_folder = os.path.abspath(os.curdir)
    repo_folder = os.path.dirname(current_folder)
    pylint_path = os.path.join(repo_folder, addon_folder)
if not os.path.exists(pylint_path):
    print('\n\tERROR: pylint folder not found:', pylint_path)
else:
    py_files_count = 0
    for root, dirs, files in os.walk(pylint_path):
        for file in files:
            name, ext = os.path.splitext(file)
            if not ext == '.py':
                continue
            path = os.path.join(root, file)
            pylint_opts = ['--rcfile=test.pylintrc', path]
            module_path = path[len(pylint_path) : ]
            if module_path[0] == os.sep:
                module_path = module_path[1 : ]
            print('\n\t\t', module_path, '\n')
            pylint.lint.Run(pylint_opts, exit=False)
            py_files_count += 1
    if not py_files_count:
        print('\n\tERROR: folder has no *.py files:', pylint_path)
