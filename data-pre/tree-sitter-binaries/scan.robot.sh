#!/bin/bash

# Directory to search in
directory="$1"

# Check if the directory is provided
if [ -z "$directory" ]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

# Find all .robot files in the directory
robot_files=($(find "$directory" -type f -name "*.robot" -o -name "*.resource"))

# Get the number of .robot files
file_count=${#robot_files[@]}

# Provide the number of files
echo "Found $file_count .robot .resource files in the directory: $directory"

# Exit if no files found
if [ "$file_count" -eq 0 ]; then
  echo "No .robot/.resource files found."
  exit 0
fi

# Loop through each .robot file and run the tt command
for file in "${robot_files[@]}"; do
  echo "Processing file: $file"
  tree-sitter parse  -sq "$file"
  if [ $? -ne 0 ]; then
    echo "Error running 'tree-sitter parse' on $file"
  fi
done

