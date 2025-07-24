# Makefile for Configurable Search QGIS Plugin

PLUGIN_NAME = configurable_search
PLUGIN_VERSION = 1.0.0

# Default target
all: resources zip

# Build Qt resources
resources:
	@echo "Building Qt resources..."
	@if command -v pyrcc5 >/dev/null 2>&1; then \
		pyrcc5 -o resources.py resources.qrc; \
		echo "Resources built successfully"; \
	else \
		echo "Warning: pyrcc5 not found. Install with: pip install PyQt5-tools"; \
	fi

# Create plugin package
zip: clean
	@echo "Creating plugin package..."
	@zip -r $(PLUGIN_NAME).zip *.py *.txt *.md *.qrc *.png 2>/dev/null || true
	@echo "Plugin package created: $(PLUGIN_NAME).zip"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -f $(PLUGIN_NAME).zip
	@rm -f *.pyc
	@rm -rf __pycache__

# Install to QGIS plugins directory (Linux/macOS)
install: all
	@echo "Installing plugin..."
	@PLUGIN_DIR="$$HOME/.local/share/QGIS/QGIS3/profiles/default/python/plugins/$(PLUGIN_NAME)"; \
	mkdir -p "$$PLUGIN_DIR"; \
	cp -r *.py *.txt *.md *.qrc *.png "$$PLUGIN_DIR/"; \
	echo "Plugin installed to $$PLUGIN_DIR"

# Development targets
dev-setup:
	@echo "Setting up development environment..."
	@pip install -r requirements.txt

lint:
	@echo "Running code linting..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 *.py; \
	else \
		echo "flake8 not found. Install with: pip install flake8"; \
	fi

# Show plugin info
info:
	@echo "Plugin: $(PLUGIN_NAME)"
	@echo "Version: $(PLUGIN_VERSION)"
	@echo "Files: $$(ls -1 *.py *.txt *.md *.qrc 2>/dev/null | wc -l) files"
	@echo "Size: $$(du -sh . | cut -f1)"

# Help target
help:
	@echo "Available targets:"
	@echo "  all        - Build resources and create zip package"
	@echo "  resources  - Build Qt resources file"
	@echo "  zip        - Create plugin zip package"
	@echo "  clean      - Remove build artifacts"
	@echo "  install    - Install plugin to QGIS plugins directory"
	@echo "  dev-setup  - Install development dependencies"
	@echo "  lint       - Run code linting"
	@echo "  info       - Show plugin information"
	@echo "  help       - Show this help message"

.PHONY: all resources zip clean install dev-setup lint info help
