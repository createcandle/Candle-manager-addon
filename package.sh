#!/bin/bash -e

version=$(grep version package.json | cut -d: -f2 | cut -d\" -f2)

if [ -z "${ADDON_ARCH}" ]; then
  TARFILE_SUFFIX=
else
  PYTHON_VERSION="$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d. -f 1-2)"
  TARFILE_SUFFIX="-${ADDON_ARCH}-v${PYTHON_VERSION}"
fi

# Clean up from previous releases
rm -rf *.tgz package SHA256SUMS lib

python -c "import json, os; \
    fname = os.path.join(os.getcwd(), 'package.json'); \
    d = json.loads(open(fname).read()); \
    d['files'] = filter(lambda x: not x.startswith('arduino-cli/') or x.startswith('arduino-cli/${ADDON_ARCH}/'), d['files']); \
    f = open(fname, 'wt'); \
    json.dump(d, f, indent=2); \
    f.close()
"

# keep only the compiled DS binary that we need
find arduino-cli -mindepth 1 -maxdepth 1 \! -name "${ADDON_ARCH}" -exec rm -rf {} \;

# Put package together
mkdir -p lib package/source/Candle_cleaner package/code/Candle_cleaner
cp source/Candle_cleaner/Candle_cleaner.ino package/source/Candle_cleaner/
cp source/Candle_cleaner/Candle_cleaner.ino package/code/Candle_cleaner/

# Pull down Python dependencies
pip3 install -r requirements.txt -t lib --no-binary :all: --prefix ""

# Put package together
cp *.py manifest.json package.json LICENSE README.md boards.txt package/
cp -r lib pkg arduino-cli css images js views package/
find package -type f -name '*.pyc' -delete
find package -type d -empty -delete

# Generate checksums
cd package
find . -type f \! -name SHA256SUMS -exec shasum --algorithm 256 {} \; >> SHA256SUMS
cd -

# Make the tarball
TARFILE="Candle-manager-addon-${version}${TARFILE_SUFFIX}.tgz"
tar czf ${TARFILE} package

shasum --algorithm 256 ${TARFILE} > ${TARFILE}.sha256sum

rm -rf SHA256SUMS package
