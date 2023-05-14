#!/bin/bash

# exit when any command fails
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

# Build the package

if test -d "dist"; then
    echo -e $CYAN"Delete current build saved"$NC
    rm -r dist
fi

echo -e $CYAN"Build the package"$NC
python3 setup.py sdist bdist_wheel

echo -e $CYAN"Save tar file"$NC
# mkdir build_package
# mv dist/*.tar.gz build_package

echo -e $CYAN"Cleaning file"$NC
rm -r *.egg-info build

# echo -e $GREEN"Build is in build_package folder !"$NC
# echo ""
# echo "You can now run:"
# echo "pip3 install build_package/*.tar.gz"

# python3 -m build     

echo -e $GREEN"Build is in dist folder !"$NC
echo ""
echo "You can now run:"
echo "pip3 install dist/*.tar.gz"
echo "To install the package locally"
echo ""
echo "Or"
echo "twine upload dist/*"
echo "To upload the package to PyPi"

