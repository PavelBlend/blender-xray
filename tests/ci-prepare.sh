#!/bin/sh
set -e

DIR="blender/$BLENDER_VERSION"
if [ ! -e "$DIR/blender" ]; then
    FROM="http://download.blender.org/release/Blender$BLENDER_VERSION"
    NONE="NONE"
    TAR="NONE"
    case "$BLENDER_VERSION" in
        "2.79")
            TBZ="blender-$BLENDER_VERSION-linux-glibc219-x86_64.tar.bz2"
            PYTHON_VERSION="3.5"
            ;;
        "3.6")
            TAR="blender-$BLENDER_VERSION.15-linux-x64.tar.xz"
            PYTHON_VERSION="3.10"
            ;;
        *)
            echo "Unsupported version: $BLENDER_VERSION"
            exit 1
            ;;
    esac
    mkdir -p "$DIR"

    echo "$NONE"
    if [ "$TAR" = "$NONE" ]; then
        wget "$FROM/$TBZ"
        tar jxf "$TBZ" -C "$DIR" --strip-components 1
    else
        wget "$FROM/$TAR"
        tar -xf "$TAR" -C "$DIR" --strip-components 1
    fi

    TGT=$HOME/.config/blender/$BLENDER_VERSION/scripts/addons
    mkdir -p $TGT
    ln -s io_scene_xray $TGT/

    wget https://files.pythonhosted.org/packages/38/df/d5e67851e83948def768d7fb1a0fd373665b20f56ff63ed220c6cd16cb11/coverage-5.5.tar.gz#md5=22e8fc8c26c46e76fb3c7f99a5f6eb92
    tar zxf coverage-5.5.tar.gz
    mv coverage-5.5/coverage "$DIR/$BLENDER_VERSION/python/lib/python$PYTHON_VERSION/"
    rm -rf coverage-5.5
fi
