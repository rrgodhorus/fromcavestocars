#!/bin/bash

# Usage: ./backup.sh 

files=("openai.cache.json" "itemdb.json" "tooldict.json" "ic.googleimage.json" "ic.pixabay.json")
backup_dir="cachebackup"

for file in "${files[@]}"; do
    if [[ ! -e "$file" ]]; then
        echo "Warning: $file does not exist, skipping."
        continue
    fi

    filename=$(basename "$file")

    # Find the next available backup number
    next_number=1
    while [[ -e "$backup_dir/${filename}.${next_number}" ]]; do
        next_number=$((next_number + 1))
    done

    # Copy the file
    cp "$file" "$backup_dir/${filename}.${next_number}"

    echo "Backup of $file created at $backup_dir/${filename}.${next_number}"
done
