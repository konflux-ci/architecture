# Konflux Architecture Makefile
# Provides targets for linting, validation, and development tasks

.PHONY: help build serve install lint lint-mermaid lint-adr-status lint-eleventy-headers install-mermaid-cli clean

help:
	@echo "Available targets:"
	@echo "  help              - Show this help message"
	@echo "  build             - Build the site locally"
	@echo "  serve             - Build and serve the site with live reload"
	@echo "  install           - Install npm dependencies"
	@echo "  lint              - Run all linting and validation"
	@echo "  lint-mermaid      - Validate Mermaid diagrams in markdown files"
	@echo "  lint-adr-status   - Validate ADR statuses in all ADR files"
	@echo "  lint-eleventy-headers - Validate Eleventy front matter in markdown files"
	@echo "  install-mermaid-cli - Install Mermaid CLI tool locally"
	@echo "  clean             - Clean up generated files"

# Install dependencies
install:
	npm install

# Build the site
build: install
	@./hack/util/generate-adr-table > ADR/index.md
	npm run build

# Serve the site with live reload
serve: install
	npm run serve

# Main lint target - runs all validation
lint: lint-mermaid lint-adr-status lint-eleventy-headers

# Mermaid diagram validation
lint-mermaid: install-mermaid-cli
	@./hack/lint-mermaid

# ADR status validation
lint-adr-status:
	@./hack/lint-adr-status

# Eleventy front matter validation
lint-eleventy-headers:
	@./hack/lint-eleventy-headers

# Install Mermaid CLI locally to user's home directory
install-mermaid-cli:
	@./hack/install-mermaid-cli

# Clean up generated files
clean:
	npm run clean
	@./hack/clean 
