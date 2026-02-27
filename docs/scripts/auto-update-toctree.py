import glob
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

SERVICES = [
    ("Foundry", "foundry"),
    ("Machine Learning", "machine-learning"),
]


def get_git_date(file_path: str) -> str | None:
    """Get the last commit date (YYYY-MM-DD) for a file using git."""
    if not file_path or not os.path.exists(file_path):
        return None
    try:
        date = (
            subprocess.check_output(
                ["git", "log", "-1", "--format=%ad", "--date=short", file_path],
                stderr=subprocess.STDOUT,
            )
            .decode("utf-8")
            .strip()
        )
        return date or None
    except Exception:
        return None


def get_notebook_creation_date(base_name: str, dir_name: str) -> datetime:
    """Get the creation date of a notebook file using git."""
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
            stat_info = os.stat(notebook_file)
            creation_time = getattr(stat_info, "st_birthtime", stat_info.st_mtime)
            return datetime.fromtimestamp(creation_time)
    except (subprocess.CalledProcessError, OSError, ValueError):
        return datetime.min


def is_notebook_new(creation_date: datetime) -> bool:
    """Check if a notebook is considered new (created in last 7 days)."""
    days_ago = datetime.now() - timedelta(days=7)
    return creation_date > days_ago


def get_original_notebook_path(mdx_file: str, dir_name: str) -> str | None:
    """Map an MDX file back to the original notebook for git date lookups."""
    base = Path(mdx_file).stem
    nb_path = f"examples/{dir_name}/{base}/azure-notebook.ipynb"
    if os.path.exists(nb_path):
        return nb_path
    return None


def parse_metadata(content: str) -> dict:
    """Parse YAML-like metadata from --- ... --- block at the top of content."""
    metadata_match = re.search(
        r"^\s*(?:<!--\s*)?---\s*\n(.*?)\n---\s*(?:\s*-->)?",
        content,
        re.DOTALL | re.MULTILINE,
    )
    if not metadata_match:
        return {}
    metadata_str = metadata_match.group(1)
    return {k.strip(): v.strip() for k, v in re.findall(r"(\w+):\s*(.+)", metadata_str)}


def strip_metadata_block(content: str) -> str:
    """Remove the --- ... --- metadata block from content."""
    content = re.sub(
        r"^\s*(?:<!--\s*)?---\s*\n.*?\n---\s*(?:\s*-->)?\s*\n",
        "",
        content,
        count=1,
        flags=re.DOTALL | re.MULTILINE,
    )
    return content.strip()


def inject_author_date(content: str, author: str | None, date: str | None) -> str:
    extra_parts = []
    if author:
        extra_parts.append(f"<small>Written by {author}</small>")
    if date:
        extra_parts.append(f"<small>Last updated {date}</small>")

    if not extra_parts:
        return content

    extra_info = "<p>" + "<br>".join(extra_parts) + "</p>"

    match = re.search(r"^(# .+)$", content, re.MULTILINE)
    if match:
        title_line = match.group(1)
        content = content.replace(title_line, f"{title_line}\n\n{extra_info}\n", 1)

    return content


def get_example_entries(dir_name: str) -> list:
    """Find, process, and sort example files for a given service directory."""
    example_files = sorted(glob.glob(f"docs/source/{dir_name}/examples/*.mdx"))
    if not example_files:
        return []

    entries = []
    for file in example_files:
        with open(file, "r+") as mdx_file:
            content = mdx_file.read()

            # Parse and remove metadata block
            metadata = parse_metadata(content)
            content = strip_metadata_block(content)

            # Get author from metadata and last-updated date from git
            author = metadata.get("author")
            original_file = get_original_notebook_path(file, dir_name)
            date = get_git_date(original_file)  # type: ignore

            # Inject author/date info into the content
            content = inject_author_date(content, author, date)

            # Write back the processed content (metadata stripped, author/date injected)
            mdx_file.seek(0)
            mdx_file.write(content)
            mdx_file.truncate()

            # Extract title from first # heading
            title = metadata.get("title")
            if not title:
                title_match = re.search(r"^# (.+)", content, re.MULTILINE)
                if title_match:
                    title = title_match.group(1).strip()

            if not title:
                print(f"WARNING: No title found in {file}")
                continue

            base = Path(file).stem

            # Get creation date for sorting
            creation_date = get_notebook_creation_date(base, dir_name)
            is_new = is_notebook_new(creation_date)

            entries.append((base, title, is_new, creation_date))

    # Sort by creation date (newest first)
    entries.sort(key=lambda x: x[3], reverse=True)
    return entries


def build_examples_section(dir_name: str, entries: list) -> list:
    """Build the YAML lines for an Examples sub-section."""
    lines = []
    lines.append("  # GENERATED CONTENT DO NOT EDIT")
    lines.append("  - sections:")
    for base, title, is_new, creation_date in entries:
        lines.append(f"    - local: {dir_name}/examples/{base}")
        lines.append(f"      title: {title}")
        # if is_new:
        #     lines.append("      new: true")
    lines.append("    title: Examples")
    # NOTE: set to true now, to improve discoverability
    lines.append("    isExpanded: true")
    lines.append("  # END OF GENERATED CONTENT")
    return lines


def inject_examples_for_service(
    lines: list, display_name: str, dir_name: str, entries: list
) -> list:
    """Inject generated example entries into an existing service section.

    If the toctree already has a section with `title: <display_name>`, the
    examples block is inserted right before that title line (so it becomes a
    nested sub-section).  If no such section exists, a brand-new top-level
    section is appended at the end of the file.
    """
    # Check whether the section already exists
    has_section = any(line.strip() == f"title: {display_name}" for line in lines)

    if has_section:
        result_lines = []
        for line in lines:
            if line.strip() == f"title: {display_name}":
                result_lines.extend(build_examples_section(dir_name, entries))
            result_lines.append(line)
        return result_lines

    # Section does not exist yet — create a whole new top-level entry.
    # The entire block is wrapped inside the generated-content markers so
    # that `make clean` can remove it completely (including the outer
    # `- sections:` and `title:` lines).
    new_section = ["# GENERATED CONTENT DO NOT EDIT"]
    new_section.append("- sections:")
    new_section.append("  - sections:")
    for base, title, is_new, creation_date in entries:
        new_section.append(f"    - local: {dir_name}/examples/{base}")
        new_section.append(f"      title: {title}")
    new_section.append("    title: Examples")
    new_section.append("    isExpanded: true")
    new_section.append(f"  title: {display_name}")
    new_section.append("  new: true")
    new_section.append("# END OF GENERATED CONTENT")
    return lines + new_section


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

    # Ensure the file ends with exactly one newline (POSIX compliant)
    output = "\n".join(lines).rstrip("\n") + "\n"
    with open(toctree_file, "w") as f:
        f.write(output)


if __name__ == "__main__":
    update_toctree_yaml()
