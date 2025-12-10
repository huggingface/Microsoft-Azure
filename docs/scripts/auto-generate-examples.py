import os
import re


def process_readme_files():
    print("Processing azure-notebook.md files from examples/foundry...")
    os.makedirs("docs/source/foundry/examples", exist_ok=True)

    for dir in ["foundry"]:
        for root, _, files in os.walk(f"examples/{dir}"):
            for file in files:
                if file == "azure-notebook.md":
                    process_file(root, file, dir)


def process_file(root, file, dir):
    file_path = os.path.join(root, file)
    subdir = root.replace(f"examples/{dir}/", "")
    base = os.path.basename(subdir)

    target = f"docs/source/foundry/examples/{base}.mdx"

    print(f"Processing {file_path} to {target}")
    with open(file_path, "r") as f:
        content = f.read()

    # For Juypter Notebooks, remove the comment i.e. `<!--` and the `--!>` but keep the metadata
    content = re.sub(r"<!-- (.*?) -->", r"\1", content, flags=re.DOTALL)

    content = re.sub(
        r"\(\./([^/)]*\.png)\)",
        r"(https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/microsoft-azure/"
        + root.replace("examples/", "")
        + r"/\1)",
        content,
    )
    content = re.sub(
        r"\(\.\./([^)]+)\)",
        r"(https://github.com/huggingface/Microsoft-Azure/tree/main/examples/"
        + dir
        + r"/\1)",
        content,
    )
    content = re.sub(
        r"\(\.\/([^)]+)\)",
        r"(https://github.com/huggingface/Microsoft-Azure/tree/main/" + root + r"/\1)",
        content,
    )

    def replacement(match) -> str:
        block_type = match.group(1)
        content = match.group(2)

        # Remove '> ' from the beginning of each line
        lines = [line[2:] for line in content.split("\n") if line.strip()]

        # Determine the Tip type
        tip_type = " warning" if block_type == "WARNING" else ""

        # Construct the new block
        new_block = f"<Tip{tip_type}>\n\n"
        new_block += "\n".join(lines)
        new_block += "\n\n</Tip>\n"

        return new_block

    # Regular expression to match the specified blocks
    pattern = r"> \[!(NOTE|WARNING)\]\n((?:>.*(?:\n|$))+)"

    # Perform the transformation
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    # Remove any remaining '>' or '> ' at the beginning of lines
    content = re.sub(r"^>[ ]?", "", content, flags=re.MULTILINE)

    # Check for remaining relative paths
    if re.search(r"\(\.\./|\(\./", content):
        print("WARNING: Relative paths still exist in the processed file.")
        print(
            "The following lines contain relative paths, consider replacing those with GitHub URLs instead:"
        )
        for i, line in enumerate(content.split("\n"), 1):
            if re.search(r"\(\.\./|\(\./", line):
                print(f"{i}: {line}")
    else:
        print("No relative paths found in the processed file.")

    # Calculate the example URL
    example_url = f"https://github.com/huggingface/Microsoft-Azure/tree/main/{root}"
    if file.__contains__("azure-notebook"):
        example_url += "/azure-notebook.ipynb"

    # Add the final note
    content += f"\n\n---\n<Tip>\n\n📍 Find the complete example on GitHub [here]({example_url})!\n\n</Tip>"

    with open(target, "w") as f:
        f.write(content)


if __name__ == "__main__":
    process_readme_files()
