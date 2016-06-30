#!/bin/sh

if [ ! -e "blender/blender" ]; then
    TBZ=blender-2.77-linux-glibc211-x86_64.tar.bz2

    mkdir -p blender
    wget http://download.blender.org/release/Blender2.77/$TBZ
    tar jxf $TBZ -C blender --strip-components 1

    TGT=$HOME/.config/blender/2.77/scripts/addons
    mkdir -p $TGT
    ln -s io_scene_xray $TGT/
fi
