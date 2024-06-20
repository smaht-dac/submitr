#!/bin/bash
# Download the most recent release of the smaht-submitr binary for the calling platform.

LATEST_RELEASE_INFO_URL=https://api.github.com/repos/smaht-dac/submitr/releases/latest
TARGET=submitr

function download_url() {
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
}

download_url
if [ -z $DOWNLOAD_URL ] ; then
    # Retry once or twice; in testing within GitHub Actions only, intermittently fails first time.
    echo "Retrying once ..."
    echo $LATEST_RELEASE_INFO_URL
        curl $LATEST_RELEASE_INFO_URL
    sleep 1
    download_url
    if [ -z $DOWNLOAD_URL ] ; then
        echo "Retrying twice ..."
        echo $DOWNLOAD_URL
        echo $LATEST_RELEASE_INFO_URL
        curl $LATEST_RELEASE_INFO_URL
        sleep 2
        download_url
        if [ -z $DOWNLOAD_URL ] ; then
            echo "Retrying thrice ..."
            echo $DOWNLOAD_URL
            echo $LATEST_RELEASE_INFO_URL
            curl -L $LATEST_RELEASE_INFO_URL
            sleep 4
            download_url
            if [ -z $DOWNLOAD_URL ] ; then
                echo "Retrying one final/fourth time ..."
                echo $DOWNLOAD_URL
                echo $LATEST_RELEASE_INFO_URL
                curl -L $LATEST_RELEASE_INFO_URL
                sleep 8
                download_url
                if [ -z $DOWNLOAD_URL ] ; then
                    echo "Failed to download: $LATEST_RELEASE_INFO_URL"
                fi
            fi
        fi
    fi
fi

echo "Downloading $DOWNLOAD_URL to $TARGET"
curl -L -s -o $TARGET $DOWNLOAD_URL
chmod a+x $TARGET
echo "Downloaded $DOWNLOAD_URL to $TARGET"
ls -l $TARGET
