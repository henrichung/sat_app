#!/bin/bash
set -e

# Ensure conda-build is available
conda install -y conda-build

# Build the conda package
conda build conda-recipe

# Export the path to the built package
export PKG_PATH=$(conda build conda-recipe --output)
echo "Package built at: $PKG_PATH"

# Optional: Convert to packages for other platforms
# conda convert --platform all $PKG_PATH -o outputdir/

echo "To install the package run:"
echo "conda install $PKG_PATH"