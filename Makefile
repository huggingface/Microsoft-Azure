.PHONY: install docs clean serve help

# Add new services here (space-separated directory names under examples/)
SERVICES := foundry machine-learning

install:
	@uv pip install hf-doc-builder requests watchdog

docs: clean
	@$(foreach svc,$(SERVICES), \
		echo "Creating docs/source/$(svc)/examples directory for examples/$(svc)..." && \
		mkdir -p docs/source/$(svc)/examples && \
		echo "Converting Jupyter Notebooks to MDX for $(svc)..." && \
		doc-builder notebook-to-mdx examples/$(svc)/ && \
	) true
	@echo "Auto-generating example files for documentation..."
	@python docs/scripts/auto-generate-examples.py
	@$(foreach svc,$(SERVICES), \
		echo "Cleaning up generated Markdown Notebook files for $(svc)..." && \
		find examples/$(svc)/ -name "azure-notebook.md" -type f -delete && \
	) true
	@echo "Generating YAML tree structure and appending to _toctree.yml..."
	@python docs/scripts/auto-update-toctree.py
	@echo "YAML tree structure appended to docs/source/_toctree.yml"
	@echo "Documentation setup complete."

clean:
	@echo "Cleaning up generated documentation..."
	@$(foreach svc,$(SERVICES), \
		rm -rf docs/source/$(svc)/examples && \
	) true
	@awk '/# GENERATED CONTENT DO NOT EDIT/,/# END OF GENERATED CONTENT/{next} {print}' docs/source/_toctree.yml > docs/source/_toctree.yml.tmp; mv docs/source/_toctree.yml.tmp docs/source/_toctree.yml
	@echo "Cleaning up generated Markdown Notebook files (if any)..."
	@$(foreach svc,$(SERVICES), \
		find examples/$(svc) -name "azure-notebook.md" -type f -delete && \
	) true
	@echo "Cleanup complete."

serve:
	@echo "Serving documentation via doc-builder"
	doc-builder preview microsoft-azure docs/source --not_python_module

help:
	@echo "Usage:"
	@echo "  make clean   - Remove the auto-generated docs"
	@echo "  make docs    - Auto-generate the examples for the docs"
	@echo "  make install - Install the required Python dependencies"
	@echo "  make serve   - Serve the docs locally at http://localhost:5173"
