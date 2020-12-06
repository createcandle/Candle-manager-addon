#!/bin/bash -e

version=$(grep '"version"' manifest.json | cut -d: -f2 | cut -d\" -f2)

# Setup environment for building inside Dockerized toolchain
[ $(id -u) = 0 ] && umask 0

# Clean up from previous releases
rm -rf *.tgz *.pyc ._* *.sha256sum package SHA256SUMS lib

if [ -z "${ADDON_ARCH}" ]; then
  TARFILE_SUFFIX=
else
  PYTHON_VERSION="$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d. -f 1-2)"
  TARFILE_SUFFIX="-${ADDON_ARCH}-v${PYTHON_VERSION}"
fi


# Put package together
mkdir -p lib package/source/Candle_cleaner package/code/Candle_cleaner
cp source/Candle_cleaner/Candle_cleaner.ino package/source/Candle_cleaner/
cp source/Candle_cleaner/Candle_cleaner.ino package/code/Candle_cleaner/

# Pull down Python dependencies
pip3 install -r requirements.txt -t lib --no-binary :all: --prefix ""

# Put package together
cp *.py manifest.json LICENSE README.md boards.txt package/
cp -r lib pkg arduino-cli css images js views package/
find package -type f -name '*.pyc' -delete
find package -type f -name '._*' -delete
find package -type d -empty -delete

cd package

# keep only the compiled DS binary that we need
find arduino-cli -mindepth 1 -maxdepth 1 \! -name "${ADDON_ARCH}" -exec rm -rf {} \;

# Generate checksums
echo "generating checksums"
find . -type f \! -name SHA256SUMS -exec shasum --algorithm 256 {} \; >> SHA256SUMS
cd -

# Make the tarball
echo "creating archive"
TARFILE="Candle-manager-addon-${version}${TARFILE_SUFFIX}.tgz"
tar czf ${TARFILE} package

shasum --algorithm 256 ${TARFILE} > ${TARFILE}.sha256sum
cat ${TARFILE}.sha256sum

#rm -rf SHA256SUMS package
