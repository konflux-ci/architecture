# Konflux Architecture Makefile
# Provides targets for linting, validation, and development tasks

.PHONY: help lint lint-mermaid lint-adr-status install-mermaid-cli clean

# Default target
help:
	@echo "Available targets:"
	@echo "  help              - Show this help message"
	@echo "  lint              - Run all linting and validation"
	@echo "  lint-mermaid      - Validate Mermaid diagrams in markdown files"
	@echo "  lint-adr-status   - Validate ADR statuses in all ADR files"
	@echo "  install-mermaid-cli - Install Mermaid CLI tool locally"
	@echo "  clean             - Clean up generated files"

# Main lint target - runs all validation
lint: lint-mermaid lint-adr-status
	@echo "✅ All linting completed successfully"

# Mermaid diagram validation
lint-mermaid: install-mermaid-cli
	@./hack/lint-mermaid

# ADR status validation
lint-adr-status:
	@./hack/lint-adr-status

# Install Mermaid CLI locally to user's home directory
install-mermaid-cli:
	@./hack/install-mermaid-cli

# Clean up generated files
clean:
	@./hack/clean 
