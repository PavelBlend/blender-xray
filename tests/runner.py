import coverage
import os
import unittest

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
