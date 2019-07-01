#!/bin/sh
set -e

[ "$BLENDER_VERSION" != "2.79" ] && exit 0
./cc-test-reporter after-build --exit-code $TRAVIS_TEST_RESULT
bash <(curl -s https://codecov.io/bash)
