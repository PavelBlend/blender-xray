import coverage
import os
import unittest
import sys

cov = coverage.Coverage(
    branch=True,
    source=['io_scene_xray'],
    omit=[
        'io_scene_xray/*_ui.py',
        'io_scene_xray/ui_*.py',
    ]
)
cov.start()

suite = unittest.defaultTestLoader.discover('.')
if not unittest.TextTestRunner().run(suite).wasSuccessful():
    exit(1)

cov.stop()
cov.xml_report()

if '--save-html-report' in sys.argv:
    cov.html_report()
