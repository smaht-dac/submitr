#!/bin/bash
BRANCH=master
BRANCH=pyinstaller-experiment-20240611
BASEURL=https://raw.githubusercontent.com/smaht-dac/submitr/$BRANCH/downloads
TARGET=/usr/local/bin/submitr

UNAME=`uname`
ARCH=`arch`
if [ $UNAME == 'Darwin' ] ; then
        URL=$BASEURL/macos/submitr
else
    if [ $ARCH == 'arm64' ] ; then
        URL=$BASEURL/linux/arm/submitr
    else
        URL=$BASEURL/linux/x86/submitr
    fi
fi

curl -L -o $TARGET $URL -s
chmod a+x $TARGET
