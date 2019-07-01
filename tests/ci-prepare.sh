#!/bin/sh
set -e

DIR="blender-$BLENDER_VERSION"
if [ ! -e "$DIR/blender" ]; then
    case "$BLENDER_VERSION" in
        "2.77")
            TBZ="blender-$BLENDER_VERSION-linux-glibc211-x86_64.tar.bz2"
            ;;
        "2.78")
            TBZ="blender-$BLENDER_VERSION-linux-glibc219-x86_64.tar.bz2"
            ;;
        "2.79")
            TBZ="blender-$BLENDER_VERSION-linux-glibc219-x86_64.tar.bz2"
            ;;
        *)
            echo "Unsupported version: $BLENDER_VERSION"
            exit 1
            ;;
    esac
    mkdir -p "$DIR"
    wget "http://download.blender.org/release/Blender$BLENDER_VERSION/$TBZ"
    tar jxf "$TBZ" -C "$DIR" --strip-components 1

    TGT=$HOME/.config/blender/$BLENDER_VERSION/scripts/addons
    mkdir -p $TGT
    ln -s io_scene_xray $TGT/

    wget https://pypi.python.org/packages/53/fe/9e0fbdbca15c2c1253379c3a694f4315a420555e7874445b06edeaeacaea/coverage-4.2.tar.gz#md5=1e09362a3f35d589f942359441050a6e
    tar zxf coverage-4.2.tar.gz
    mv coverage-4.2/coverage "$DIR/$BLENDER_VERSION/python/lib/python3.5/"
    rm -rf coverage-4.2
fi
