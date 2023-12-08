import os
import le


# search *.part files

part_files = []

for root, dirs, files in os.walk(os.curdir):

    for file in files:
        ext = os.path.splitext(file)[-1]

        if ext == '.part':
            path = os.path.join(root, file)
            path = os.path.abspath(path)
            part_files.append(path)

# dump files

for path in reversed(part_files):
    le.part.dump_main(path)
