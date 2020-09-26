#!/bin/sh
set -e

DIR="blender/$BLENDER_VERSION"
if [ ! -e "$DIR/blender" ]; then
    FROM="http://download.blender.org/release/Blender$BLENDER_VERSION"
    PYTHON_VERSION="3.5"
    NONE="NONE"
    TAR="NONE"
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
        "2.80")
            TBZ="blender-$BLENDER_VERSION-linux-glibc217-x86_64.tar.bz2"
            PYTHON_VERSION="3.7"
            ;;
        "2.81")
            TBZ="blender-$BLENDER_VERSION-linux-glibc217-x86_64.tar.bz2"
            PYTHON_VERSION="3.7"
            ;;
        "2.82")
            TAR="blender-$BLENDER_VERSION-linux64.tar.xz"
            PYTHON_VERSION="3.7"
            ;;
        "2.83")
            TAR="blender-$BLENDER_VERSION.0-linux64.tar.xz"
            PYTHON_VERSION="3.7"
            ;;
        "2.90")
            TAR="blender-$BLENDER_VERSION.1-linux64.tar.xz"
            PYTHON_VERSION="3.7"
            ;;
        "2.91")
            FROM="https://builder.blender.org/download"
            HTML=$(curl $FROM/)
            if [[ "$HTML" =~ blender-$BLENDER_VERSION.0-[a-z0-9]+-linux64.tar.xz ]]; then
                TAR="${BASH_REMATCH[0]}"
            else
                echo "Cannot parse file name from: $HTML"
                exit 1
            fi
            PYTHON_VERSION="3.7"
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

    wget https://pypi.python.org/packages/53/fe/9e0fbdbca15c2c1253379c3a694f4315a420555e7874445b06edeaeacaea/coverage-4.2.tar.gz#md5=1e09362a3f35d589f942359441050a6e
    tar zxf coverage-4.2.tar.gz
    mv coverage-4.2/coverage "$DIR/$BLENDER_VERSION/python/lib/python$PYTHON_VERSION/"
    rm -rf coverage-4.2
fi
