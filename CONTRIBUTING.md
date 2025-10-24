# Contributing to Konflux Architecture Documentation

## Overview

This repository contains architecture documentation, ADRs, and diagrams. All changes require peer-reviewed pull requests.

## Pull Request Requirements

**Significant architectural changes:**
- Update overview docs and diagrams
- Add ADR to `/ADR/` folder
- Require 2+ approvals

**Corrections/clarifications:**
- Update overview docs and diagrams
- Add `skip-adr-check` label
- Require 1+ approval

## Maintaining CLAUDE.md Structure

When adding new services or ADRs, update these files to keep Claude agent context optimized:

### Adding a New Service

1. **Create service documentation**
   - Location: `/architecture/core/[service].md` OR `/architecture/add-ons/[service].md`
   - Include `local_summary:` frontmatter:
     ```yaml
     ---
     title: Service Name
     eleventyNavigation:
       key: Service Name
       parent: Core Services  # or Add-ons
       order: N
     toc: true
     local_summary:
       scope: "One-line description of what service does"
       key_crds: "CRD1, CRD2, CRD3"
       depends_on: "service1, service2" # or "None (foundational)"
       related_adrs: "ADR-XXXX (brief context), ADR-YYYY (brief context)"
       key_concepts: "Key terms, important patterns, unique mechanisms"
     ---
     ```

2. **Update `/architecture/CLAUDE.md`**
   - Add to `Core Services` or `Add-ons` list
   - Format: `` `filename.md` - Brief description (< 10 words)``
   - Maintain alphabetical order within section

3. **Update published index pages**
   - `/architecture/core/index.md` OR `/architecture/add-ons/index.md`
   - Add service summary with link in "Service (Component) Context" section
   - Update mermaid diagrams to show new service's interactions with existing services
   - Update both "Application Context" and "Service (Component) Context" diagrams as needed

4. **Update main overview** (if architecturally significant)
   - `/architecture/index.md`

### Adding a New ADR

1. **Create ADR file**
   - Location: `/ADR/NNNN-description.md`
   - Follow template: `/ADR/0000-adr-template.md`
   - Include: Status, Context, Decision, Consequences

2. **Update `/ADR/INDEX.md`**
   - Add entry with:
     - ADR number and title
     - Status (Proposed, Implementable, Implemented, Superseded, etc.)
     - One-sentence context summary (first sentence from Context section)
     - 2-4 topic keywords
   - Maintain numerical order

3. **Update service frontmatter** (if service-specific)
   - Add to `related_adrs:` field in affected service(s)
   - Format: `"ADR-XXXX (brief context)"`

## local_summary: Frontmatter Guidelines

Keep frontmatter concise - agents read this frequently:

- **scope**: One line, < 100 characters, describes what service does
- **key_crds**: Comma-separated CRD names (just the resource type, not full API)
- **depends_on**: Services required for this service to function
- **related_adrs**: Relevant ADRs with brief parenthetical context
- **key_concepts**: Important terminology, patterns, unique features

**Note:** The `index.md` files in `/architecture/core/` and `/architecture/add-ons/` use `eleventyNavigation` frontmatter instead of `local_summary:` frontmatter. These are overview/aggregation files that should NOT be listed in CLAUDE.md's service lists and should only be read when understanding multi-service interactions.

## File Structure Reference

```
/
├── CLAUDE.md                    # Agent navigation & loading strategy
├── CONTRIBUTING.md              # This file
├── README.md                    # Repository overview
├── /architecture/
│   ├── CLAUDE.md               # Duplicate for subagents in architecture/
│   ├── index.md                # Main published architecture doc
│   ├── /core/
│   │   ├── index.md            # Published core services overview
│   │   └── [service].md        # Individual service docs (with local_summary: frontmatter)
│   └── /add-ons/
│       ├── index.md            # Published add-ons overview
│       └── [service].md        # Individual add-on docs (with local_summary: frontmatter)
├── /ADR/
│   ├── INDEX.md                # Searchable ADR catalog (agents use this!)
│   └── NNNN-*.md               # Individual ADRs
└── /diagrams/                  # SVG diagrams (draw.io format)
```

## What NOT to Include in CLAUDE.md

- Detailed service descriptions → use service files
- ADR details → use `/ADR/INDEX.md`
- Examples and tutorials → bloats agent context
- Diagrams → visual only, not text-consumable
- Maintenance procedures → this file

## Questions?

See existing services and ADRs for examples, or ask in pull request reviews.
