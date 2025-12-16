# How to contribute to `huggingface/Microsoft-Azure`

## How to contribute with an example?

If you are willing to contribute with a Microsoft Foundry example, or even just update / fix an existing example you can do so by simply updating the Jupyter Notebook, making sure you match the following:

- When you push your changes you don't leak any of your Azure keys.
- Clean output of all cells before pushing.
- Add images within the same directory as the `azure-notebook.ipynb` (those will be excluded by the `.gitignore`), and make sure that you upload the images with the same directory structure under https://huggingface.co/datasets/huggingface/documentation-images/tree/main/microsoft-azure.
    - Make sure that the image references are relative to the Jupyter Notebook during development, since those will be automatically formatted to rely on the images from the Hugging Face Hub repository aforementioned.
    - If you don't update or change the images, feel free to skip / ignore this point.
- Make sure to follow the same style as the existing examples, there's no such thing as a template, but all the examples are pretty similar in style, so ideally follow the same style for any new example.
- As an optional check, you are recommended to run `codespell` (or any other grammar checks) before you push the content to make sure that is well-written.

If alternatively you'd like us to build an example that you have in mind or that you'd like to see, you can always [open an issue](https://github.com/huggingface/Microsoft-Azure/issues/new) describing the example and we'll do our best to build it if interesting.
