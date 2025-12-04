# Contributing to Konflux Architecture

Thank you for your interest in contributing to the Konflux Architecture documentation. This document provides guidelines and instructions for contributing to this repository.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Types of Contributions](#types-of-contributions)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [ADR Guidelines](#adr-guidelines)
- [Style Guidelines](#style-guidelines)
- [Testing Your Changes](#testing-your-changes)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone git@github.com:YOUR_USERNAME/konflux-ci-architecture.git`
3. Add the upstream remote: `git remote add upstream git@github.com:konflux-ci/konflux-ci-architecture.git`
4. Create a branch for your changes: `git checkout -b your-feature-branch`

## Types of Contributions

### Significant Changes

Significant changes include modifications to technical details or architecture. These require:

1. Changes to the overview document and diagrams where applicable
2. An ADR (Architecture Decision Record) added to the `/ADR` folder
3. At least 2 approvals to be merged

Examples of significant changes:
- New architectural patterns or approaches
- Changes to core system design
- Introduction of new components or services
- Modifications to existing service contracts

### Corrections and Clarifications

Minor changes that improve clarity without changing technical decisions require:

1. Changes to the overview document and diagrams where applicable
2. The `skip-adr-check` label on your pull request
3. At least 1 approval to be merged

Examples of corrections/clarifications:
- Fixing typos or grammar
- Improving documentation clarity
- Updating outdated links
- Correcting formatting issues

## Development Setup

### Prerequisites

- Node.js 22 or later
- npm (comes with Node.js)
- Git
- A text editor that supports EditorConfig

### Installation

Install project dependencies:

```bash
make install
```

Or directly with npm:

```bash
npm install
```

## Making Changes

### Local Development

Build the site locally:

```bash
make build
```

Serve the site with live reload for development:

```bash
make serve
```

The site will be available at `http://localhost:8080` (default Eleventy port).

### Working with Architecture Documents

Architecture documents are located in the `/architecture` folder:
- `/architecture/core/` - Core Konflux services
- `/architecture/add-ons/` - Add-on services and controllers

When updating architecture documents:
1. Ensure changes align with the overall architecture vision
2. Update related diagrams if applicable
3. Cross-reference related ADRs
4. Follow the established document structure

### Working with Diagrams

Diagrams are stored in the `/diagrams` folder:
- Use [draw.io](https://draw.io) for creating/editing diagrams
- Save diagrams in SVG format
- Use descriptive filenames
- Place diagrams in service-specific subdirectories when applicable

### Creating an ADR

For significant changes, create an Architecture Decision Record:

1. Check the ADR template at `/ADR/0000-adr-template.md`
2. Review the new ADR process at [konflux-ci/community/ADRs.md](https://github.com/konflux-ci/community/blob/main/ADRs.md)
3. Number your ADR sequentially (check existing ADRs for the next number)
4. Use the format: `XXXX-brief-description.md`
5. Include the following sections:
   - Title and date
   - Status (Proposed, Accepted, Implemented, Superseded, etc.)
   - Context
   - Decision
   - Consequences

## Pull Request Process

### Before Submitting

1. Run the linter to ensure all validations pass:
   ```bash
   make lint
   ```

2. Build the site to verify no build errors:
   ```bash
   make build
   ```

### Submitting Your Pull Request

1. Push your changes to your fork
2. Open a pull request against the `main` branch
3. Fill out the pull request template (if available)
4. Ensure your PR title is clear and descriptive
5. Add appropriate labels:
   - Use `skip-adr-check` for minor corrections/clarifications
   - For significant changes, ensure you've included an ADR
6. Request reviews from relevant code owners (automatically assigned via CODEOWNERS)

### PR Review Process

- Code owners will be automatically requested for review based on the files changed
- Address reviewer feedback promptly
- Keep your branch up to date with the main branch
- Ensure all CI checks pass

### Code Owners

The repository uses CODEOWNERS for automatic review assignment:
- `/ADR/` - Konflux Governance Committee (@konflux-ci/kgc)
- Service-specific paths have dedicated maintainer teams
- General changes require review from @konflux-ci/book-publishers

## ADR Guidelines

### ADR Numbering

- Use sequential numbers starting from 0001
- Check for duplicate numbers using: `make lint-adr-numbers`
- Do not renumber existing ADRs unless explicitly reorganizing

### ADR Status

Valid ADR statuses include:
- Proposed
- Accepted
- Implemented
- Superseded
- Deprecated
- Rejected

Validate ADR statuses with:
```bash
make lint-adr-status
```

## Style Guidelines

### Markdown Formatting

- Use 2 spaces for indentation (enforced by EditorConfig)
- End files with a newline
- Trim trailing whitespace
- Use UTF-8 encoding
- Use LF (Unix-style) line endings

### Mermaid Diagrams

- Validate Mermaid syntax using: `make lint-mermaid`
- Keep diagrams simple and focused
- Add comments to explain complex flows
- Test diagram rendering locally before submitting

### Eleventy Front Matter

- Include required front matter in markdown files
- Validate headers with: `make lint-eleventy-headers`
- Follow the existing pattern in similar documents

## Testing Your Changes

Run all validations before submitting:

```bash
make lint
```

This runs:
- `lint-mermaid` - Validates Mermaid diagrams
- `lint-adr-status` - Validates ADR statuses
- `lint-adr-numbers` - Checks for duplicate ADR numbers
- `lint-eleventy-headers` - Validates Eleventy front matter

Build the site to ensure no errors:

```bash
make build
```

## Getting Help

- Review existing ADRs in `/ADR` for examples
- Check the architecture overview at `/architecture/index.md`
- Refer to the ADR template at `/ADR/0000-adr-template.md`
- Ask questions in pull request comments

## Additional Resources

- [ADR Process Documentation](https://github.com/konflux-ci/community/blob/main/ADRs.md)
- [Eleventy Documentation](https://www.11ty.dev/docs/)
- [Mermaid Documentation](https://mermaid.js.org/)
- [EditorConfig](https://editorconfig.org/)

Thank you for contributing to Konflux Architecture documentation!
