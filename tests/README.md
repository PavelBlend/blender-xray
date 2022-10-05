# The Test Suite
This directory contains files and modules which are used to ensure the quality of code and algorithms.

## Installing the Required Packages
To run tests from this directory the following components are required:
- [Blender](http://www.blender.org/) - see the wiki for a list of [supported versions](https://github.com/PavelBlend/blender-xray/wiki#supported-blender-versions).
- [Coverage](https://pypi.python.org/pypi/coverage) - required for gathering a statistics which lines of code are covered with tests.
This package should be installed within blender embedded python rather than a system-wide one.
To do this, you could download the package archive and extract the `coverage` folder (which contains the `__init__.py` file) from the archive into the blender embedded python directory (`bender-installation-directory`/`blender-version`/python/lib/`python-version`).

## Running the Tests
To run all tests, invoke the `runner.py` script from the repository-root directory using `blender`:

```shell
blender --factory-startup -noaudio -b --python tests/runner.py --save-html-report output_folder
```
The `output_folder` parameter is optional. If all tests are passed, the `./htmlcov/` directory with coverage reports will be created.

To start tests for all `blender` versions, you can use such commands for `windows`:

```shell
del .coverage
C:\progs\blender\277\blender.exe --factory-startup -noaudio -b --python tests/runner.py --save-html-report htmlcov\277\
C:\progs\blender\278\blender.exe --factory-startup -noaudio -b --python tests/runner.py --save-html-report htmlcov\278\
C:\progs\blender\279\blender.exe --factory-startup -noaudio -b --python tests/runner.py --save-html-report htmlcov\279\
C:\progs\blender\280\blender.exe --factory-startup -noaudio -b --python tests/runner.py --save-html-report htmlcov\280\
C:\progs\blender\281\blender.exe --factory-startup -noaudio -b --python tests/runner.py --save-html-report htmlcov\281\
C:\progs\blender\282\blender.exe --factory-startup -noaudio -b --python tests/runner.py --save-html-report htmlcov\282\
C:\progs\blender\283\blender.exe --factory-startup -noaudio -b --python tests/runner.py --save-html-report htmlcov\283\
C:\progs\blender\290\blender.exe --factory-startup -noaudio -b --python tests/runner.py --save-html-report htmlcov\290\
C:\progs\blender\291\blender.exe --factory-startup -noaudio -b --python tests/runner.py --save-html-report htmlcov\291\
C:\progs\blender\292\blender.exe --factory-startup -noaudio -b --python tests/runner.py --save-html-report htmlcov\292\
C:\progs\blender\293\blender.exe --factory-startup -noaudio -b --python tests/runner.py --save-html-report htmlcov\293\
C:\progs\blender\301\blender.exe --factory-startup -noaudio -b --python tests/runner.py --save-html-report htmlcov\301\
C:\progs\blender\312\blender.exe --factory-startup -noaudio -b --python tests/runner.py --save-html-report htmlcov\312\
C:\progs\blender\321\blender.exe --factory-startup -noaudio -b --python tests/runner.py --save-html-report htmlcov\321\
C:\progs\blender\330\blender.exe --factory-startup -noaudio -b --python tests/runner.py --save-html-report htmlcov\330\
```

All coverage files will be merged and saved to the last folder (in this case `htmlcov\330\`).


## Creating the Tests
Sometimes, a test requires a sample data file which should be stored in this repository.
Please, keep in mind, the sample files are always downloaded on `git clone` command, whenever the user wants to download them or not.
So, please, keep these files as small as possible.
