.PHONY: install serve help

install:
	@uv pip install hf-doc-builder requests watchdog

serve:
	@echo "Serving documentation via doc-builder"
	doc-builder preview microsoft-azure docs/source --not_python_module

help:
	@echo "Usage:"
	@echo "  make install - Install the required Python dependencies"
	@echo "  make serve   - Serve the docs locally at http://localhost:5173"
