#!/bin/bash

set -e

version=$(grep version package.json | cut -d: -f2 | cut -d\" -f2)

# Clean up from previous releases
rm -rf *.tgz package
rm -f SHA256SUMS

# Put package together
mkdir package
mkdir package/source
mkdir package/source/Candle_cleaner
mkdir package/code
mkdir package/code/Candle_cleaner
cp source/Candle_cleaner/Candle_cleaner.ino package/source/Candle_cleaner/Candle_cleaner.ino
cp source/Candle_cleaner/Candle_cleaner.ino package/code/Candle_cleaner/Candle_cleaner.ino
cp -r pkg LICENSE arduino-cli boards.txt package.json *.py requirements.txt setup.cfg package/
find package -type f -name '*.pyc' -delete
find package -type d -empty -delete
echo "prepared the files in the package directory"

# Generate checksums
cd package
sha256sum *.py pkg/*.py LICENSE requirements.txt setup.cfg > SHA256SUMS
cd -
echo "generated checksums"

# Make the tarball
tar czf "Candle-manager-${version}.tgz" package
sha256sum "Candle-manager-${version}.tgz"

