import os
import le


# search *.level files

scene_files = []

for root, dirs, files in os.walk(os.curdir):

    for file in files:
        ext = os.path.splitext(file)[-1]

        if ext == '.level':
            path = os.path.join(root, file)
            path = os.path.abspath(path)
            scene_files.append(path)

# dump files

for path in reversed(scene_files):
    le.selection.dump_main(path)
