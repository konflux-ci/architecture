# Konflux Architecture Makefile
# Provides targets for linting, validation, and development tasks

.PHONY: help build serve install lint lint-mermaid lint-adr-status lint-adr-numbers lint-eleventy-headers lint-frontmatter lint-agents-md install-mermaid-cli clean

help:
	@echo "Available targets:"
	@echo "  help              - Show this help message"
	@echo "  build             - Build the site locally"
	@echo "  serve             - Build and serve the site with live reload"
	@echo "  install           - Install npm dependencies"
	@echo "  lint              - Run all linting and validation"
	@echo "  lint-agents-md    - Validate AGENTS.md line counts are accurate"
	@echo "  lint-mermaid      - Validate Mermaid diagrams in markdown files"
	@echo "  lint-adr-status   - Validate ADR statuses in all ADR files"
	@echo "  lint-adr-numbers  - Check for duplicate ADR numeric identifiers"
	@echo "  lint-eleventy-headers - Validate Eleventy front matter in markdown files"
	@echo "  lint-frontmatter     - Validate frontmatter schemas and cross-references"
	@echo "  install-mermaid-cli - Install Mermaid CLI tool locally"
	@echo "  clean             - Clean up generated files"

# Install dependencies
install:
	npm install

# Build the site
build: install
	rm -rf ./_site/*
	@./hack/util/generate-adr-table > ADR/index.md
	npm run build

# Serve the site with live reload
serve: install
	npm run serve

# Main lint target - runs all validation
lint: lint-mermaid lint-adr-status lint-adr-numbers lint-eleventy-headers lint-frontmatter lint-agents-md

# Mermaid diagram validation
lint-mermaid: install-mermaid-cli
	@./hack/lint-mermaid

# ADR status validation
lint-adr-status:
	@./hack/lint-adr-status

# ADR number uniqueness validation
lint-adr-numbers:
	@./hack/lint-adr-numbers

# Eleventy front matter validation
lint-eleventy-headers:
	@./hack/lint-eleventy-headers

# Frontmatter schema and cross-reference validation
lint-frontmatter:
	@python3 ./hack/lint-frontmatter

# AGENTS.md line count validation
lint-agents-md:
	@./hack/lint-agents-md

# Install Mermaid CLI locally to user's home directory
install-mermaid-cli:
	@./hack/install-mermaid-cli

# Clean up generated files
clean:
	npm run clean
	@./hack/clean 
