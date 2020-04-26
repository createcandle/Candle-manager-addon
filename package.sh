#!/bin/bash

set -e

version=$(grep version package.json | cut -d: -f2 | cut -d\" -f2)

# Clean up from previous releases
rm -rf *.tgz package
rm -f SHA256SUMS
rm -rf ._*

# Put package together
mkdir package
mkdir package/source
mkdir package/source/Candle_cleaner
mkdir package/code
mkdir package/code/Candle_cleaner
cp source/Candle_cleaner/Candle_cleaner.ino package/source/Candle_cleaner/Candle_cleaner.ino
cp source/Candle_cleaner/Candle_cleaner.ino package/code/Candle_cleaner/Candle_cleaner.ino

# Pull down Python dependencies
pip3 install -r requirements.txt -t lib --no-binary flask,pyserial,requests --prefix ""


cp *.py manifest.json package.json LICENSE README.md boards.txt requirements.txt setup.cfg  package/
cp -r lib pkg arduino-cli css images js views package/
find package -type f -name '*.pyc' -delete
find package -type d -empty -delete
echo "prepared the files in the package directory"

# Generate checksums
cd package
find . -type f \! -name SHA256SUMS -exec sha256sum {} \; >> SHA256SUMS
#sha256sum *.py pkg/*.py LICENSE requirements.txt setup.cfg > SHA256SUMS
cd ..
echo "generated checksums"

# Make the tarball
tar czf "Candle-manager-addon-${version}.tgz" package
sha256sum "Candle-manager-addon-${version}.tgz"


