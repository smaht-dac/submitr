#!/bin/bash
BASEURL=https://github.com/smaht-dac/submitr/releases/download/latest/submitr
TARGET=submitr

UNAME=`uname`
ARCH=`arch`
if [ $UNAME == 'Darwin' ] ; then
        URL=$BASEURL-macos
else
    if [ $ARCH == 'arm64' -o $ARCH == 'aarch64' ] ; then
        URL=$BASEURL-linux-arm
    else
        URL=$BASEURL-linux-x86
    fi
fi

curl -L -o $TARGET $URL -s
chmod a+x $TARGET
ls -l $TARGET
