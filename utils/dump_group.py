import os
import le


# search *.group files

group_files = []

for root, dirs, files in os.walk(os.curdir):

    for file in files:
        ext = os.path.splitext(file)[-1]

        if ext == '.group':
            path = os.path.join(root, file)
            path = os.path.abspath(path)
            group_files.append(path)

# dump files

for path in reversed(group_files):

    with open(path, 'rb') as file:
        data = file.read()

    print('dump file: "{}"'.format(path))
    le.group.dump_group(data)
