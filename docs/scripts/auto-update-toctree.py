import glob
import re
from pathlib import Path


def update_toctree_yaml():
    toctree_file = "docs/source/_toctree.yml"

    # Read existing _toctree.yml as raw text
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
    example_files = sorted(glob.glob("docs/source/azure-ml/examples/*.mdx"))

    if not example_files:
        print("No example files found")
        # Write back the cleaned content without examples
        with open(toctree_file, "w") as f:
            f.write(content)
        return

    # Build example entries
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

            example_entries.append((base, title))

    if not example_entries:
        print("No valid example entries found")
        return

    # Now we need to find the Azure ML section and add the Examples section to it
    lines = content.split("\n")
    result_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        result_lines.append(line)
        
        # Look for the Azure ML section
        if line.strip() == "title: Azure ML":
            # Add the Examples section before the title
            result_lines.pop()  # Remove the "title: Azure ML" line we just added
            
            # Add the Examples section with proper markers
            result_lines.append("  # GENERATED CONTENT DO NOT EDIT")
            result_lines.append("  - sections:")
            for base, title in example_entries:
                result_lines.append(f"    - local: azure-ml/examples/{base}")
                result_lines.append(f"      title: {title}")
            result_lines.append("    title: Examples")
            result_lines.append("    isExpanded: false")
            result_lines.append("  # END OF GENERATED CONTENT")
            
            # Now add the "title: Azure ML" line
            result_lines.append(line)
        
        i += 1

    # Write the updated content
    with open(toctree_file, "w") as f:
        f.write("\n".join(result_lines))


if __name__ == "__main__":
    update_toctree_yaml()