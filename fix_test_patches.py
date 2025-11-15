#!/usr/bin/env python3
"""
Fix test mock patch paths by removing 'src.' prefix to match source code import style.
"""

import os
import re
from pathlib import Path

def fix_patches_in_file(file_path):
    """Fix patch paths in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content

    # Pattern to match patch("src.module") or @patch("src.module")
    pattern = r'patch\("src\.([^"]+)"\)'
    replacement = r'patch("\1")'

    new_content = re.sub(pattern, replacement, content)

    if new_content != original_content:
        # Print what we're changing
        matches = re.findall(pattern, original_content)
        for match in matches:
            print(f"  {file_path.name}: 'src.{match}' -> '{match}'")

        with open(file_path, 'w') as f:
            f.write(new_content)
        return True
    return False

def main():
    """Fix patch paths in all test files."""
    test_dir = Path('tests')

    # Find all Python test files
    test_files = list(test_dir.glob('**/*.py'))

    print(f"Found {len(test_files)} test files")
    print("Fixing patch paths...")

    modified_count = 0
    for test_file in sorted(test_files):
        if fix_patches_in_file(test_file):
            modified_count += 1

    print(f"\nModified {modified_count} files")
    print("Patch fixes complete!")

if __name__ == '__main__':
    main()