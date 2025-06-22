#!/bin/bash
# Pull from upstream - copies example data files to root directory
# This sets up the local development environment with sample data

echo "Pulling from upstream (copying example data files)..."

# Files to copy from exampledatafiles/ to root
files=(
    "ic.googleimage.json"
    "ic.pixabay.json" 
    "itemstomake.txt"
    "openai.cache.json"
    "problems.log"
    "testcache.json"
)

# Copy individual files
for file in "${files[@]}"; do
    if [[ -f "exampledatafiles/$file" ]]; then
        cp "exampledatafiles/$file" .
        echo "✓ Copied $file"
    else
        echo "✗ Warning: exampledatafiles/$file not found"
    fi
done

# Copy directories
if [[ -d "exampledatafiles/instance" ]]; then
    cp -r "exampledatafiles/instance" .
    echo "✓ Copied instance/ directory"
else
    echo "✗ Warning: exampledatafiles/instance not found"
fi

if [[ -d "exampledatafiles/static" ]]; then
    mkdir -p static
    cp -r exampledatafiles/static/* static/
    echo "✓ Copied static files"
else
    echo "✗ Warning: exampledatafiles/static not found"
fi

echo ""
echo "Upstream pull completed!"
echo "Run './check_upstream_data.py' to verify all files are present."