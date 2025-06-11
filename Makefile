serve:
	@echo "Serving documentation via doc-builder"
	doc-builder preview microsoft-azure docs/source --not_python_module

help:
	@echo "Usage:"
	@echo "  make docs   - Auto-generate the examples for the docs"
