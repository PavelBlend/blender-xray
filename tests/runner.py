import coverage
import os
import unittest
import sys

cov = coverage.Coverage()
try:
    cov.load()
except:
    pass
cov.combine(keep=True)
cov.start()

suite = unittest.defaultTestLoader.discover('.')
if not unittest.TextTestRunner().run(suite).wasSuccessful():
    exit(1)

cov.stop()
cov.xml_report()

if '--save-html-report' in sys.argv:
    save_html_index = sys.argv.index('--save-html-report')
    if len(sys.argv) > save_html_index:
        save_directory = sys.argv[save_html_index + 1]
        cov.html_report(directory=save_directory)
    else:
        cov.html_report()
