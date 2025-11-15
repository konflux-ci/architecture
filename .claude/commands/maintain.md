Audit and automatically fix architecture documentation inconsistencies.

This command will:
1. Detect issues in service lists, frontmatter, and ADR references
2. Automatically fix all issues found
3. Analyze service relationships when new services are added
4. Report all changes made

**All fixes are applied automatically - no user intervention required.**

## Execution Steps

### 1. Service List Maintenance

**Check:** Services in CLAUDE.md vs actual files

**Auto-fixes:**
- Missing services → Add to CLAUDE.md with scope from frontmatter
- Phantom services → Remove from CLAUDE.md
- Order issues → Re-sort alphabetically

**Actions:**
```
For each .md file in /architecture/core/ and /architecture/add-ons/:
  - If NOT in CLAUDE.md → Extract scope, add entry in alphabetical order
  - Report: "✓ Added [service].md to CLAUDE.md"
  - TRIGGER: Service relationship analysis (see step 1b)

For each service listed in CLAUDE.md:
  - If file doesn't exist → Remove from CLAUDE.md
  - Report: "✓ Removed [service].md from CLAUDE.md (file not found)"
```

### 1b. Service Relationship Analysis (ALL services)

**When:** Always - analyze relationships for all services

**Relationship Detection Criteria:**
1. **Content references**: Service documentation mentions another service by name or links to it
2. **CRD usage**: Service uses or mentions CRDs owned by another service
3. **CRD ownership**: Service owns CRDs that another service uses
4. **Shared ADRs**: Services reference same ADRs (functional overlap)
5. **Explicit listing**: Service B lists service A (implies bidirectional)

**Actions for NEW services (not yet in CLAUDE.md):**
```
1. Scan service content for ALL references to other services:
   - Service names mentioned in text (e.g., "build-service", "Integration Service")
   - Links to other service files (e.g., [Build Service](./build-service.md))
   - CRD names that belong to other services
   - ADRs shared with other services

2. AUTO-FIX: Add all discovered relationships to related_services
   - Report: "✓ [new-service].md: added [list] to related_services (detected from content)"

3. AUTO-FIX: Update existing services that should reference the new service
   - If existing service mentions new service's CRDs → add to related_services
   - If existing service explicitly mentions new service name → add to related_services
   - Report: "✓ [existing-service].md: added [new-service] to related_services"
```

**Actions for EXISTING services (already in CLAUDE.md):**
```
1. Scan service content for references to other services

2. Identify missing relationships (detected but not in related_services)

3. PROMPT user for each missing relationship:

   Example prompt:
   ┌─────────────────────────────────────────────────────────────┐
   │ Potential relationship detected:                             │
   │                                                              │
   │ Service: build-service.md                                   │
   │ Missing relation: image-controller                          │
   │                                                              │
   │ Evidence:                                                    │
   │ • Content mentions "image-controller" 3 times               │
   │ • Line 45: "uses image-controller for repository setup"    │
   │ • Line 89: "integrates with image-controller via..."       │
   │ • Shares ADR-0047 (caching)                                 │
   │                                                              │
   │ Add image-controller to build-service.md related_services?  │
   │ (y/n):                                                       │
   └─────────────────────────────────────────────────────────────┘

4. If user confirms (y):
   - Add to related_services
   - Report: "✓ Added [service] to [target].md based on user confirmation"

5. If user declines (n):
   - Skip
   - Report: "○ Skipped adding [service] to [target].md (user declined)"

6. Check for bidirectional gaps:
   If ServiceA → ServiceB but ServiceB ↛ ServiceA:
     - Prompt: "ServiceA references ServiceB. Add reverse link? (y/n)"
     - Show evidence why reverse might make sense
     - Apply based on user response
```

**Special handling for NEW services:**
- NEW services get ALL detected relationships auto-added (user can remove later)
- EXISTING services that should reference the NEW service get auto-updated
- Rationale: New service documentation clearly shows its dependencies/interactions


### 2. Service Frontmatter Validation

**Check:** Each service has complete `overview:` frontmatter

**Auto-fixes:**
- Missing overview section → Create with intelligent defaults
- Missing fields → Add with content-based suggestions

**Actions:**
```
For each service file:
  If missing overview section:
    - Create overview: with all required fields
    - Use title for scope
    - Scan content for CRDs, related services, ADRs
    - Report: "✓ Added overview section to [service].md"

  For each required field (scope, key_crds, related_services, related_adrs, key_concepts):
    If missing:
      - Analyze file content to generate field value
      - For related_services: scan ALL other services for relationships
      - Add to overview section
      - Report: "✓ Added [field] to [service].md"
```

### 3. ADR Quick-Reference Maintenance

**Check:** All ADR files are indexed in quick-reference.md

**Auto-fixes:**
- Missing ADRs → Extract Status/Decision/Topics and add entry
- Order issues → Re-sort numerically

**Actions:**
```
For each ADR/NNNN-*.md file (except template and quick-reference.md):
  If NOT in quick-reference.md:
    - Extract Status from ## Status section
    - Extract first substantive sentence from ## Decision section
    - Generate Topics from filename and content keywords
    - Add entry in numerical order
    - Report: "✓ Added ADR-NNNN to quick-reference.md"

Verify each entry has Status, Summary, Topics:
  If missing:
    - Read ADR file and extract missing information
    - Update entry
    - Report: "✓ Completed ADR-NNNN entry in quick-reference.md"
```

### 4. ADR Reference Validation

**Check:** All ADR references in service frontmatter point to existing files

**Auto-fixes:**
- Broken references → Remove from related_adrs field

**Actions:**
```
For each service with related_adrs:
  Extract all ADR-NNNN references
  For each reference:
    If ADR/NNNN-*.md doesn't exist:
      - Remove reference from related_adrs
      - Report: "✓ Removed broken reference ADR-NNNN from [service].md"
```

## Output Format

Provide clear summary of all fixes:

```
🔧 MAINTENANCE COMPLETE

Auto-fixes applied:

✓ Service Lists (N fixes)
  - Added: service1.md, service2.md
  - Removed: phantom-service.md
  - Re-sorted: Core Services alphabetically

✓ Service Relationships (N fixes)
  - Analyzed new service: service1.md
  - Updated service1.md related_services: added pipeline-service, build-service
  - Updated build-service.md related_services: added service1
  - Updated integration-service.md related_services: added service1

✓ Service Frontmatter (N fixes)
  - Added overview to: service2.md
  - Added key_concepts to: service3.md
  - Added related_services to: service4.md

✓ ADR Index (N fixes)
  - Added to quick-reference.md: ADR-0056, ADR-0057
  - Updated entries: ADR-0023 (added Topics)

✓ ADR References (N fixes)
  - Removed broken references: ADR-9999 from build-service.md

Summary:
- Core Services: 7
- Add-ons: 5
- ADRs: 53
- Total fixes: 12

All documentation is now consistent with service relationships updated.
```

## Relationship Analysis Algorithm

```
function analyzeServiceRelationships(newService):
  relationships = []

  # Read new service content
  content = read(newService)
  newServiceCRDs = extract(content, "key_crds")
  newServiceMentions = extract(content, service names)
  newServiceADRs = extract(content, "related_adrs")

  # Check each existing service
  for existingService in allServices:
    shouldRelate = false

    # Check if new service mentions existing service
    if existingService.name in newServiceMentions:
      shouldRelate = true

    # Check if new service uses existing service's CRDs
    if existingService.CRDs intersects newServiceCRDs:
      shouldRelate = true

    # Check if new service shares ADRs (functional overlap)
    if existingService.ADRs intersects newServiceADRs:
      shouldRelate = true

    # Reverse check: does existing service mention new service?
    if newService.name in read(existingService):
      shouldRelate = true
      # Also update existing service to reference new service
      updateRelatedServices(existingService, add newService)

    # Check if existing service uses new service's CRDs
    if newServiceCRDs intersects existingService.CRDs:
      shouldRelate = true
      updateRelatedServices(existingService, add newService)

    if shouldRelate:
      relationships.add(existingService)

  # Update new service with discovered relationships
  updateRelatedServices(newService, relationships)

  return relationships
```

## Implementation Notes

- Use Edit tool for surgical changes to preserve formatting
- Maintain alphabetical order in CLAUDE.md
- Maintain numerical order in quick-reference.md
- Extract frontmatter using proper YAML parsing
- For relationship analysis: read all services once, cache in memory
- Be conservative with generated content - use file content as source
- Always report what was changed and why
- Service relationship analysis is bidirectional - update both services
