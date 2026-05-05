# Contributing to Konflux Architecture

Thank you for your interest in contributing to the Konflux Architecture documentation. This document provides guidelines and instructions for contributing to this repository.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Types of Contributions](#types-of-contributions)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Testing Your Changes](#testing-your-changes)
- [Adding a New Service](#adding-a-new-service)
- [Adding a New ADR](#adding-a-new-adr)

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

For details on the ADR process at [konflux-ci/community/ADRs.md](https://github.com/konflux-ci/community/blob/main/ADRs.md)

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
- Python 3 with PyYAML (for frontmatter linting)
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
- `lint-frontmatter` - Validates frontmatter schemas and cross-references
- `lint-agents-md` - Validates AGENTS.md file line counts and completeness

Build the site to ensure no errors:

```bash
make build
```

## Adding a New Service

1. **Create service documentation** in `/architecture/core/[service].md` or `/architecture/add-ons/[service].md` with `overview:` frontmatter:
   ```yaml
   ---
   title: Service Name
   eleventyNavigation:
     key: Service Name
     parent: Core Services  # or Add-ons
     order: N
   toc: true
   overview:
     scope: "One-line description of what service does"
     key_crds:
       - CRDName1
       - CRDName2
     related_services:
       - other-service
     related_adrs:
       - "NNNN"
     key_concepts:
       - concept one
       - concept two
   ---
   ```

2. **Update published index pages** (`/architecture/core/index.md` or `/architecture/add-ons/index.md`) — add service summary and update mermaid interaction diagrams.

3. **Update main overview** (`/architecture/index.md`) if architecturally significant.

4. **Run `make lint-frontmatter`** to verify the frontmatter is valid and cross-references are consistent.

## Adding a New ADR

1. **Create ADR file** at `/ADR/NNNN-description.md` following the template at `/ADR/0000-adr-template.md`. Include frontmatter:
   ```yaml
   ---
   title: "NNNN. ADR Title"
   status: Proposed
   applies_to:
     - service-name   # or "*" if cross-cutting
   topics:
     - keyword1
     - keyword2
   ---
   ```

2. **Update service frontmatter** for affected services — add the ADR number to `related_adrs` in each service's `overview:` block. The `lint-frontmatter` check will warn about missing bidirectional references.

3. **Run `make lint-frontmatter`** to verify the ADR frontmatter is valid and references are consistent.

Note: frontmatter indexing can be done by maintainers after merge if needed. The key requirement is the ADR content itself.

## Frontmatter Reference

### Service docs (`overview:` block)

All fields except `scope` must be YAML lists:

- **scope** (string): One line, < 100 characters
- **key_crds** (list): CRD resource type names
- **related_services** (list): Service filenames without `.md` (e.g., `build-service`). Use `[]` if standalone.
- **related_adrs** (list): 4-digit ADR numbers as strings (e.g., `"0047"`). This is a curated list of the most important ADRs for understanding the service, not an exhaustive backlink — agents discover all applicable ADRs by grepping the ADR `applies_to` field directly.
- **key_concepts** (list): Important terminology and patterns

### ADR docs

- **title** (string): Must match the `# NN. Title` heading
- **status** (string): One of Accepted, Implemented, Implementable, Proposed, Replaced, Superseded, Deprecated, Approved, In consideration
- **applies_to** (list): Service filenames without `.md`, or `"*"` for cross-cutting
- **topics** (list): 2-4 keywords
- **supersedes** (list, optional): ADR numbers this supersedes
- **superseded_by** (list, optional): ADR numbers that supersede this

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
