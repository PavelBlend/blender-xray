#!/bin/sh

if [ ! -e "blender/blender" ]; then
    TBZ=blender-2.77-linux-glibc211-x86_64.tar.bz2

    mkdir -p blender
    wget http://download.blender.org/release/Blender2.77/$TBZ
    tar jxf $TBZ -C blender --strip-components 1

    TGT=$HOME/.config/blender/2.77/scripts/addons
    mkdir -p $TGT
    ln -s io_scene_xray $TGT/

    wget http://pypi.python.org/packages/53/fe/9e0fbdbca15c2c1253379c3a694f4315a420555e7874445b06edeaeacaea/coverage-4.2.tar.gz#md5=1e09362a3f35d589f942359441050a6e
    tar zxf coverage-4.2.tar.gz
    mv coverage-4.2/coverage blender/2.77/python/lib/python3.5/
    rm -rf coverage-4.2
fi
