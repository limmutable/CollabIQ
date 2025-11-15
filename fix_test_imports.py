#!/usr/bin/env python3
"""
Fix test imports by removing 'src.' prefix to match source code import style.
This resolves isinstance() failures caused by module namespace mismatches.
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content

    # Pattern to match "from src.X import Y" or "import src.X"
    patterns = [
        (r'^from src\.([a-z_]+)', r'from \1'),  # from src.module import ...
        (r'^import src\.([a-z_]+)', r'import \1'),  # import src.module
    ]

    lines = content.split('\n')
    modified_lines = []

    for line in lines:
        modified_line = line
        for pattern, replacement in patterns:
            if re.match(pattern, line.strip()):
                modified_line = re.sub(pattern, replacement, line.strip())
                # Preserve original indentation
                indent = len(line) - len(line.lstrip())
                modified_line = ' ' * indent + modified_line
                print(f"  {file_path.name}: '{line.strip()}' -> '{modified_line.strip()}'")
        modified_lines.append(modified_line)

    new_content = '\n'.join(modified_lines)

    if new_content != original_content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        return True
    return False

def main():
    """Fix imports in all test files."""
    test_dir = Path('tests')

    # Find all Python test files
    test_files = list(test_dir.glob('**/*.py'))

    print(f"Found {len(test_files)} test files")
    print("Fixing imports...")

    modified_count = 0
    for test_file in sorted(test_files):
        if fix_imports_in_file(test_file):
            modified_count += 1

    print(f"\nModified {modified_count} files")
    print("Import fixes complete!")

if __name__ == '__main__':
    main()