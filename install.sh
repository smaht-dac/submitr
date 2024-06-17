#!/bin/bash
LATEST_RELEASE_INFO_URL=https://api.github.com/repos/smaht-dac/submitr/releases/latest
TARGET=submitr

UNAME=`uname`
ARCH=`arch`
if [ $UNAME == 'Darwin' ] ; then
    if [ $ARCH == 'arm64' -o $ARCH == 'aarch64' ] ; then
        FILE=submitr-macos-arm
    else
        FILE=submitr-macos-x86
    fi
else
    if [ $ARCH == 'arm64' -o $ARCH == 'aarch64' ] ; then
        FILE=submitr-linux-arm
    else
        FILE=submitr-linux-x86
    fi
fi

DOWNLOAD_URL=`curl -L -s $LATEST_RELEASE_INFO_URL | sed -nE "s/.*\"browser_download_url\": \"(https:\/\/[^\"]*$FILE)\".*/\1/p"`
echo "Downloading $DOWNLOAD_URL to $TARGET"
curl -L -s -o $TARGET $DOWNLOAD_URL
chmod a+x $TARGET
echo "Downloaded $DOWNLOAD_URL to $TARGET"
ls -l $TARGET
