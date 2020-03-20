# The Test Suite
This directory contains files and modules which are used to ensure the quality of code and algorithms.

## Installing the Required Packages
To run tests from this directory the following components are required:
- [Blender](http://www.blender.org/) - the version should be at least as specified in the [addon info](../io_scene_xray/__init__.py).
- [Coverage](https://pypi.python.org/pypi/coverage) - required for gathering a statistics which lines of code are covered with tests.
This package should be installed within bender embedded python rather than a system-wide one.
To do this, you could download the package archive and extract the `coverage` folder (which contains the `__init__.py` file) from the archive into the blender embedded python directory (`bender-installation-directory`/`blender-version`/python/lib/`python-version`).

## Running the Tests
To run all tests, invoke the `runner.py` script from the repository-root directory using `blender`:

```shell
blender --factory-startup -noaudio -b --python tests/runner.py --save-html-report output_folder
```
The output_folder parameter is optional. If all tests are passed, the `./htmlcov/` directory with coverage reports will be created.

## Creating the Tests
Sometimes, a test requires a sample data file which should be stored in this repository.
Please, keep in mind, the sample files are always downloaded on `git clone` command, whenever the user wants to download them or not.
So, please, keep these files as small as possible.
