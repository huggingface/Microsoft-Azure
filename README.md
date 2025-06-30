# Hugging Face on Microsoft Azure

Hugging Face collaborates with Microsoft Azure across open science, open source, and cloud, to enable companies and individuals to build their own AI with the latest open models from Hugging Face and the latest infrastructure features from Microsoft Azure.

![Hugging Face on Microsoft Azure](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/microsoft-azure/thumbnail.png)

This repository contains the documentation for Hugging Face on Microsoft Azure (Azure ML, Azure AI Foundry), and how the Azure community can benefit from our partnership, as well as including detailed examples ranging a lot of different scenarios and use-cases, all leveraging open-source models and solutions within the Microsoft Azure robust and secure infrastructure.

## Documentation

The Hugging Face on Microsoft Azure documentation lives at https://hf.co/docs/microsoft-azure

## Setup

Python +3.11 and your preferred dependency manager

```bash
uv venv --python 3.11
uv pip install -r requirements.txt
```

Then you can leverage the `Makefile`:

```bash
$ make help
Usage:
  make docs   - Auto-generate the examples for the docs
  make clean  - Remove the auto-generated docs
  make serve  - Serve the docs locally at http://localhost:5173
```

> [!WARNING]
> The preview for the index won't show, and the documentation won't be rendered as it would
> within the https://hf.co/docs/microsoft-azure. To make sure that you are able to preview the
> docs, just create a PR and the `doc-builder` bot will build those and comment with the URL
> of the docs pointing to your PR.

> [!WARNING]
> When contributing note that the examples available at https://hf.co/docs/microsoft-azure
> are dynamically generated from the `examples/` directory when building the docs, so if
> you want to either add or update any example, you need to directly edit those under `examples/`.
>
> Additionally, you need to be aware and run `make clean` to prevent the auto-generated
> content from being pushed into `main`.
