import os
import sys


utils_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.dirname(utils_dir)
sys.path.append(repo_dir)


def read_file(file_path):
    with open(file_path, 'rb') as file:
        data = file.read()
    return data
