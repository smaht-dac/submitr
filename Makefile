clean:
	rm -rf *.egg-info

clear-poetry-cache:  # clear poetry/pypi cache. for user to do explicitly, never automatic
	poetry cache clear pypi --all

configure:  # does any pre-requisite installs
	pip install poetry==1.4.2

lint:
	flake8 submitr

build:  # builds
	make configure
	poetry install

test:
	pytest -m "not integration"

test-integration:
	# pytest -vv submitr/tests/test_rclone_support.py
	pytest -m integration

retest:  # runs only failed tests from the last test run. (if no failures, it seems to run all?? -kmp 17-Dec-2020)
	pytest -vv --last-failed

update:  # updates dependencies
	poetry update

tag-and-push:  # tags the branch and pushes it
	@scripts/tag-and-push

preview-locally: doc-view

doc:
	sphinx-build -b html docs/source docs/html

doc-view: doc
	open docs/html/index.html

doc-gen docgen gendoc:
	# python docs/scripts/gendoc.py --env smaht-local
	python docs/scripts/gendoc.py --env data
	make doc

publish:
	# New Python based publish script in dcicutils (2023-04-25).
	poetry run publish-to-pypi

publish-for-ga:
	# New Python based publish script in dcicutils (2023-04-25).
	poetry run publish-to-pypi --noconfirm

# This exe stuff is experimental. The pyinstaller utility allows the creation of a self-contained
# executable which can be run without Python or anything like that being installed. Have separate
# executables for MacOS and x86_64 and arm64 architectures of Linux (via docker). We do the builds
# locally; the MacOS version using native MacOS (M1) which ASSUMES we using for local builds; and
# we use docker to do x86_64 and arm64 Linux build; and note that we use docker RedHat/CentOS
# flavors of Linux, as binaries built here run on Debian/Ubuntu flavors, but not vice versa.
#
# Builds for this need to be run locally, where local means MacOS M1+, and not in GitHub Actions,
# because we obviously need to build the MacOS version on MacOS, and GitHub Actions runs on Linux;
# supposedly GitHub Actions can also do MacOS but couldn't get it totally working. And for Linux,
# we CAN use GitHub Actions for the docker based x86_64 build, but could not get it working for
# the arm64 version (exec format error). So for simplicity just build all binary versions locally.
# Binaries are written to (and checked into) the binaries directory; with a symbolic from a
# version-named file to the unversion-named file; do it like this so we don't end up with
# a ton of binaries checked in for different binary versions which haven't actually changed.
#
# There is a GitHub Actions workflow (main-binaries-release.yml) to "release" the binaries. 
# This workflow ONLY runs when a NON-beta tag is created. And it makes sure that the binaries
# which are checked in (to the binaries directory) are for this version; if not then the
# release build will fail.
#
# To install (on MacOS or Linux x86_64 or Linux arm64):
# curl https://raw.githubusercontent.com/smaht-dac/submitr/master/install.sh | /bin/bash
#
# Could also create a MacOS (pkg) installer (see exe-macos-installer in commit 42ec17dc),
# but won't easily work without signing via Apple Developer's License; so nevermind that.
#
# TODO: Figure out if we need a separate build/executable for non-M1 MacOS.

exe: exe-macos exe-linux

exe-macos:
	# Download/use with (once merged with master)
	# curl https://raw.githubusercontent.com/smaht-dac/submitr/master/install.sh | /bin/bash
	# curl https://raw.githubusercontent.com/smaht-dac/submitr/pyinstaller-experiment-20240611/install.sh | /bin/bash
	pip install poetry
	poetry install
	python -m submitr.scripts.submitr version # xyzzy
	pip install pyinstaller
	pyinstaller --onefile --name submitr ./submitr/scripts/submitr.py
	mkdir -p ./binaries
	mv ./dist/submitr ./binaries/submitr-macos
	chmod a+x ./binaries/submitr-macos
	rm -rf ./build ./dist

exe-linux: exe-linux-x86 exe-linux-arm

exe-linux-x86:
	# Download/use with (once merged with master):
	# curl https://raw.githubusercontent.com/smaht-dac/submitr/master/install.sh | /bin/bash
	# curl https://raw.githubusercontent.com/smaht-dac/submitr/pyinstaller-experiment-20240611/install.sh | /bin/bash
	# N.B. Turns out binaries built on RedHat (CentOS) work on Debian (Ubuntu); but not vice versa.
	docker build -t pyinstaller-linux-x86-build -f Dockerfile-for-pyinstaller-x86 .
	# docker buildx build -t pyinstaller-linux-x86-build -f Dockerfile-for-pyinstaller-x86 .
	mkdir -p ./binaries
	echo xyzzy docker debug
	docker ps
	docker images
	echo xyzzy end docker debug
	docker run --rm -v ./binaries:/output pyinstaller-linux-x86-build sh -c "cp /app/dist/submitr /output/submitr-linux-x86"
	# chmod a+x ./binaries/submitr-linux-x86

exe-linux-arm:
	# Download/use with (once merged with master):
	# curl https://raw.githubusercontent.com/smaht-dac/submitr/master/install.sh | /bin/bash
	# curl https://raw.githubusercontent.com/smaht-dac/submitr/pyinstaller-experiment-20240611/install.sh | /bin/bash
	# N.B. Turns out binaries built on RedHat (CentOS) work on Debian (Ubuntu); but not vice versa.
	# NOTE: Use linux/arm64 for GA
	# docker build --platform linux/arm64/v8 -t pyinstaller-linux-arm-build -f Dockerfile-for-pyinstaller-arm .
	docker build --platform linux/arm64 -t pyinstaller-linux-arm-build -f Dockerfile-for-pyinstaller-arm .
	mkdir -p ./binaries
	echo xyzzy docker debug
	docker ps
	docker images
	echo xyzzy end docker debug
	docker run --platform linux/arm64/v8 --rm -v ./binaries:/output pyinstaller-linux-arm-build sh -c "cp /app/dist/submitr /output/submitr-linux-arm"
	# chmod a+x ./binaries/submitr-linux-arm

exe-linux-arm-for-ga:
	# Download/use with (once merged with master):
	# curl https://raw.githubusercontent.com/smaht-dac/submitr/master/install.sh | /bin/bash
	# curl https://raw.githubusercontent.com/smaht-dac/submitr/pyinstaller-experiment-20240611/install.sh | /bin/bash
	# N.B. Turns out binaries built on RedHat (CentOS) work on Debian (Ubuntu); but not vice versa.
	docker buildx create --use
	docker buildx build --platform linux/arm64 -t pyinstaller-linux-arm-build -f Dockerfile-for-pyinstaller-arm .
	mkdir -p ./binaries
	echo xyzzy docker debug
	docker ps
	docker images
	echo xyzzy end docker debug
	docker run --platform linux/arm64 --rm -v ./binaries:/output pyinstaller-linux-arm-build:latest sh -c "cp /app/dist/submitr /output/submitr-linux-arm"
	# chmod a+x ./binaries/submitr-linux-arm

help:
	@make info

info:
	@: $(info Here are some 'make' options:)
	   $(info - Use 'make configure' to install poetry, though 'make build' will do it automatically.)
	   $(info - Use 'make lint' to check style with flake8.)
	   $(info - Use 'make build' to install dependencies using poetry.)
	   $(info - Use 'make preview-locally' to build and a local doc tree and open it for preview.)
	   $(info - Use 'make publish' to publish this library, but only if auto-publishing has failed.)
	   $(info - Use 'make retest' to run failing tests from the previous test run.)
	   $(info - Use 'make test' to run tests with the normal options we use for CI/CD like GA.)
	   $(info - Use 'make update' to update dependencies (and the lock file))
	   $(info - Use 'make clear-poetry-cache' to clear the poetry pypi cache if in a bad state. (Safe, but later recaching can be slow.))
