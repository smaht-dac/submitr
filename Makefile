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

# This exe stuff is experimental. The pyinstaller utility allows the creation of a self-contained executable
# which can be run without Python or anything like that being installed. If used will have to create separate
# executables for Mac and Linu; and possible M1 vs non-M1 Macs and possibly x86_64 vs arm64 Linux; for now just
# create here MacOS M1 (actually only by virtue of running this on an M1) and Linux x86, via docker. And also
# creating a Mac (pkg) installer, but won't easily work unless we get an Apple Developer's License and sign it.

exe: exe-macos exe-macos-installer exe-linux-x86 # exe-linux-arm

exe-macos: build
	# Download/use with (once merged with master)
	# curl -o submitr https://raw.githubusercontent.com/smaht-dac/submitr/master/downloads/macos/submitr
	# chmod a+x submitr
	pyinstaller --onefile --name submitr ./submitr/scripts/submitr.py
	mkdir -p ./downloads/macos
	mv ./dist/submitr ./downloads/macos/submitr
	chmod a+x ./downloads/macos/submitr
	rm -rf ./build ./dist

exe-macos-installer: exe-macos
	# Download/install with (once merged with master)
	# curl -o submitr.installer.pkg https://raw.githubusercontent.com/smaht-dac/submitr/master/downloads/macos/submitr.installer.pkg
	# Run (double click on) submitr.install.pkg
	# However error/warning about unknown developer; need a MacOS developer license and key et cetera.
	mkdir -p ./downloads/macos/installer/package/usr/local/bin ./downloads/macos/installer/scripts
	cp ./downloads/macos/submitr ./downloads/macos/installer/package/usr/local/bin
	echo "#!/bin/bash\nchmod a+x /usr/local/bin/submitr" > ./downloads/macos/installer/scripts/postinstall
	chmod a+x ./downloads/macos/installer/scripts/postinstall
	pkgbuild --root ./downloads/macos/installer/package --identifier edu.harvard.hms --version 1.0 \
		--install-location / --scripts ./downloads/macos/installer/scripts ./downloads/macos/submitr.installer.pkg
	rm -rf ./downloads/macos/installer

exe-linux-amd: build
	# Download/use with (once merged with master):
	# curl -o submitr https://raw.githubusercontent.com/smaht-dac/submitr/master/downloads/linux/x86/submitr
	# chmod a+x submitr
	docker build --build-arg ARCHITECTURE=x86 -t pyinstaller-linux-build -f Dockerfile-for-pyinstaller .
	mkdir -p ./downloads/linux/x86
	docker run --rm -v ./downloads/linux/x86:/output pyinstaller-linux-build sh -c "cp /app/dist/submitr /output/"
	chmod a+x ./downloads/linux/x86/submitr

exe-linux-x86: exe-linux-amd

exe-linux-arm: build
	# Note that this, pyinstaller for Linux ARM architecture, does NOT seem to work, at least where
	# it was tried (on a GCE t2a-standard-1 Ampere Altra instance); getting below message; searching
	# around it is said the pyinstaller is not officially supported for ARM architectures. Oh well.
	# [2546] Failed to load Python shared library '/tmp/_MEIIWRHEC/libpython3.9.so.1.0': dlopen:
	# /lib/aarch64-linux-gnu/libm.so.6: version `GLIBC_2.35' not found (required by /tmp/_MEIIWRHEC/libpython3.9.so.1.0)
	# Download/use with (once merged with master):
	# curl -o submitr https://raw.githubusercontent.com/smaht-dac/submitr/master/downloads/linux/arm/submitr
	# chmod a+x submitr
	# docker build --build-arg ARCHITECTURE=arm64v8 -t pyinstaller-linux-build -f Dockerfile-for-pyinstaller .
	# mkdir -p ./downloads/linux/arm
	# docker run --rm -v ./downloads/linux/arm:/output pyinstaller-linux-build sh -c "cp /app/dist/submitr /output/"
	# chmod a+x ./downloads/linux/arm/submitr
	echo "Not yet supported." 

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
