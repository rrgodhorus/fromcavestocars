#!/usr/bin/env python3
"""
Check if upstream data has been properly copied from exampledatafiles/
This script verifies that all necessary files have been copied to the root directory.
"""

import os
import sys

def check_file_exists(filename, description):
    """Check if a file exists and print status"""
    exists = os.path.exists(filename)
    status = "✓" if exists else "✗"
    print(f"{status} {filename} - {description}")
    return exists

def main():
    print("Checking upstream data files...")
    print("=" * 50)
    
    files_to_check = [
        ("ic.googleimage.json", "Google Image search cache"),
        ("ic.pixabay.json", "Pixabay image search cache"),
        ("itemstomake.txt", "List of items to make"),
        ("openai.cache.json", "OpenAI API response cache"),
        ("problems.log", "Problems log file"),
        ("testcache.json", "Test cache file"),
        ("instance/fctc.db", "Application database"),
        ("static/images/items/", "Item images directory")
    ]
    
    all_present = True
    for filename, description in files_to_check:
        if not check_file_exists(filename, description):
            all_present = False
    
    print("=" * 50)
    if all_present:
        print("✓ All upstream data files are present!")
        print("The repository is ready for development.")
        return 0
    else:
        print("✗ Some upstream data files are missing.")
        print("Run: cp -r exampledatafiles/* .")
        print("to copy missing files from the example data directory.")
        return 1

if __name__ == "__main__":
    sys.exit(main())