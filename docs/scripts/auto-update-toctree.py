import glob
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Add new services here as ("Display Name", "directory-name")
SERVICES = [
    ("Foundry", "foundry"),
    ("Machine Learning", "machine-learning"),
]


def get_notebook_creation_date(base_name: str, dir_name: str) -> datetime:
    """Get the creation date of a notebook file using git"""
    notebook_pattern = f"examples/{dir_name}/*/{base_name}/azure-notebook.ipynb"
    notebook_files = glob.glob(notebook_pattern)

    if not notebook_files:
        notebook_pattern = f"examples/{dir_name}/*/azure-notebook.ipynb"
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


def get_example_entries(dir_name: str) -> list:
    """Find and sort example files for a given service directory."""
    example_files = sorted(glob.glob(f"docs/source/{dir_name}/examples/*.mdx"))
    if not example_files:
        return []

    entries = []
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
            creation_date = get_notebook_creation_date(base, dir_name)
            is_new = is_notebook_new(creation_date)

            entries.append((base, title, is_new, creation_date))

    # Sort by creation date (newest first)
    entries.sort(key=lambda x: x[3], reverse=True)
    return entries


def inject_examples_for_service(
    lines: list, display_name: str, dir_name: str, entries: list
) -> list:
    """Inject generated example entries before the title line of a service section."""
    result_lines = []
    for line in lines:
        if line.strip() == f"title: {display_name}":
            result_lines.append("  # GENERATED CONTENT DO NOT EDIT")
            result_lines.append("  - sections:")
            for base, title, is_new, creation_date in entries:
                result_lines.append(f"    - local: {dir_name}/examples/{base}")
                result_lines.append(f"      title: {title}")
                # if is_new:
                #     result_lines.append("      new: true")
            result_lines.append("    title: Examples")
            # NOTE: set to true now, to improve discoverability
            result_lines.append("    isExpanded: true")
            result_lines.append("  # END OF GENERATED CONTENT")
        result_lines.append(line)
    return result_lines


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

    lines = content.split("\n")

    for display_name, dir_name in SERVICES:
        entries = get_example_entries(dir_name)
        if not entries:
            print(f"No example files found for {display_name}")
            continue
        lines = inject_examples_for_service(lines, display_name, dir_name, entries)

    with open(toctree_file, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    update_toctree_yaml()
