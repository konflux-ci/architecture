# Architecture of Konflux

This repository contains the technical and architecture documents for Konflux.
User documentation is out of scope.

## Guide to Sections

### The Technical Overview Document

[/architecture](./architecture/index.md) folder hosts the technical overview document. This document represents the latest state of agreed technical and architectural decisions. See [contributing](#contributing) on how to propose changes.

[/ref](./ref/index.md) folder hosts the API references for all the related services. These API references are generated during publish flow.

### Architecture Diagrams

[/diagrams](./diagrams/) folder stores the diagrams used on the overview document. These diagrams are done using [draw.io](https://draw.io) and stored in _.svg_ format.

### Architecture Decision Records - ADRs
[/ADR](./ADR/) folder contains the ADRs that are executed as part of the process to update these documents as explained in [contributing](#contributing) section.

## Contributing

All changes to the documents and diagrams require a peer-reviewed pull request.

For significant changes that include changes to technical details or architecture the pull request should have
1. Changes to the overview document and diagrams where applicable.
2. An ADR record is added to the `/ADR` folder.
3. At least 2 approvals to be merged

The changes that are corrections and clarifications and that do not reflect a significant change pull request should have
1. Changes to the overview document and diagrams where applicable.
2. Should have a `skip-adr-check` label
3. At least 1 approval

