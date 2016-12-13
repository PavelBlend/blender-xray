import coverage
import os
import unittest
import sys

cov = coverage.Coverage(
    branch=True,
    source=['io_scene_xray'],
)
cov.start()

suite = unittest.defaultTestLoader.discover('.')
if not unittest.TextTestRunner().run(suite).wasSuccessful():
    exit(1)

cov.stop()
cov.xml_report()

if '--save-html-report' in sys.argv:
    cov.html_report()
