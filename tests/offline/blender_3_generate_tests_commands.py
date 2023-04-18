import os


blend_folder = 'C:\\progs\\blender\\'
command = '{0} --factory-startup -noaudio -b --python tests/runner.py --save-html-report htmlcov\\{1}\\\n'
commands = []
commands.append('del .coverage\n')

for root, dirs, files in os.walk(blend_folder):
    for file in files:
        if file == 'blender.exe':
            path = os.path.join(root, file)
            dir_name = os.path.basename(root)
            ver = dir_name.split('-')[1]
            cmd = command.format(path, ver)
            commands.append(cmd)

commands.append('pause\n\n')

with open('run_tests.bat', 'w') as file:
    for line in commands:
        file.write(line)

input('Press Enter...')
