# Download the most recent release of the smaht-submitr binary for the calling platform.

# This GITHUB_TOKEN for the authorization header for curl is ONLY
# to make testing from within GitHub Actions work consistently; without
# this would intermittently get an error like: API rate limit exceeded for 13.105.117.6
GITHUB_TOKEN=$1
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
    if [ -z "$GITHUB_TOKEN" ]; then
        DOWNLOAD_URL=`curl -L -s $LATEST_RELEASE_INFO_URL | sed -nE "s/.*\"browser_download_url\": \"(https:\/\/[^\"]*$FILE)\".*/\1/p"`
    else
        DOWNLOAD_URL=`curl -H "Authorization: token $GITHUB_TOKEN" -L -s $LATEST_RELEASE_INFO_URL | sed -nE "s/.*\"browser_download_url\": \"(https:\/\/[^\"]*$FILE)\".*/\1/p"`
    fi
}

download_url
if [ -z $DOWNLOAD_URL ] ; then
    # Retry once or twice; in testing within GitHub Actions only, intermittently fails first time.
    sleep 1
    download_url
    if [ -z $DOWNLOAD_URL ] ; then
        sleep 2
        download_url
        if [ -z $DOWNLOAD_URL ] ; then
            sleep 4
            download_url
            if [ -z $DOWNLOAD_URL ] ; then
                sleep 8
                download_url
                if [ -z $DOWNLOAD_URL ] ; then
                    exit 1
                fi
            fi
        fi
    fi
fi

echo "Downloading $DOWNLOAD_URL to $TARGET"
if [ -z "$GITHUB_TOKEN" ]; then
    curl -L -s -o $TARGET $DOWNLOAD_URL
else
    curl -H "Authorization: token ${GITHUB_TOKEN}" -L -s -o $TARGET $DOWNLOAD_URL
fi
chmod a+x $TARGET
echo "Downloaded $DOWNLOAD_URL to $TARGET"
ls -l $TARGET
