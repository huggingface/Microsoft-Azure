import glob
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


def get_notebook_creation_date(base_name: str) -> datetime:
    """Get the creation date of a notebook file using git"""
    notebook_pattern = f"examples/foundry/*/{base_name}/azure-notebook.ipynb"
    notebook_files = glob.glob(notebook_pattern)

    if not notebook_files:
        notebook_pattern = "examples/foundry/*/azure-notebook.ipynb"
        all_notebooks = glob.glob(notebook_pattern)

        for notebook in all_notebooks:
            if base_name in notebook:
                notebook_files = [notebook]
                break

    if not notebook_files:
        return datetime.min

    notebook_file = notebook_files[0]

    # Get the creation time using git log to find when the file was first added
    try:
        result = subprocess.run(
            ["git", "log", "--format=%ct", "--diff-filter=A", "--", notebook_file],
            capture_output=True,
            text=True,
            check=True,
        )

        if result.stdout.strip():
            creation_timestamp = int(result.stdout.strip().split("\n")[-1])
            return datetime.fromtimestamp(creation_timestamp)
        else:
            # If git log doesn't return anything, file might be untracked or new
            stat_info = os.stat(notebook_file)
            creation_time = getattr(stat_info, "st_birthtime", stat_info.st_mtime)
            return datetime.fromtimestamp(creation_time)
    except (subprocess.CalledProcessError, OSError, ValueError):
        return datetime.min


def is_notebook_new(creation_date: datetime) -> bool:
    """Check if a notebook is considered new (created in last 7 days)"""
    days_ago = datetime.now() - timedelta(days=7)
    return creation_date > days_ago


def update_toctree_yaml():
    toctree_file = "docs/source/_toctree.yml"

    with open(toctree_file, "r") as f:
        content = f.read()

    # Remove any existing generated content between markers
    content = re.sub(
        r"^\s*# GENERATED CONTENT DO NOT EDIT.*?^\s*# END OF GENERATED CONTENT\n?",
        "",
        content,
        flags=re.MULTILINE | re.DOTALL,
    )

    # Clean up any extra newlines that might be left
    content = content.strip() + "\n"

    # Find and sort example files
    example_files = sorted(glob.glob("docs/source/foundry/examples/*.mdx"))
    if not example_files:
        print("No example files found")
        with open(toctree_file, "w") as f:
            f.write(content)
        return

    example_entries = []
    for file in example_files:
        with open(file, "r") as mdx_file:
            file_content = mdx_file.read()

            # Extract title from first line starting with "# "
            title_match = re.search(r"^# (.+)", file_content, re.MULTILINE)
            if not title_match:
                print(f"WARNING: No title found in {file}")
                continue

            title = title_match.group(1).strip()
            base = Path(file).stem

            # Get creation date and check if new
            creation_date = get_notebook_creation_date(base)
            is_new = is_notebook_new(creation_date)

            example_entries.append((base, title, is_new, creation_date))

    if not example_entries:
        print("No valid example entries found")
        return

    # Sort by creation date (newest first)
    example_entries.sort(key=lambda x: x[3], reverse=True)

    # Now we need to find the Foundry section and add the Examples section to it
    lines = content.split("\n")
    result_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        result_lines.append(line)

        # Look for the Foundry section
        if line.strip() == "title: Foundry":
            # Add the Examples section before the title
            result_lines.pop()  # Remove the "title: Foundry" line we just added

            # Add the Examples section with proper markers
            result_lines.append("  # GENERATED CONTENT DO NOT EDIT")
            result_lines.append("  - sections:")
            for base, title, is_new, creation_date in example_entries:
                result_lines.append(f"    - local: foundry/examples/{base}")
                result_lines.append(f"      title: {title}")
                # if is_new:
                #     result_lines.append("      new: true")
            result_lines.append("    title: Examples")
            # NOTE: set to true now, to improve discoverability
            result_lines.append("    isExpanded: true")
            result_lines.append("  # END OF GENERATED CONTENT")

            result_lines.append(line)

        i += 1

    with open(toctree_file, "w") as f:
        f.write("\n".join(result_lines))


if __name__ == "__main__":
    update_toctree_yaml()
