Audit the architecture documentation for consistency:

1. Compare service lists:
   - Extract services from CLAUDE.md (Core Services and Add-ons sections)
   - List actual .md files in /architecture/core/ and /architecture/add-ons/
   - Report any files missing from CLAUDE.md or listed but don't exist

2. Check service frontmatter:
   - For each service .md file, verify it has a `overview:` frontmatter section
   - Verify each overview section has: scope, key_crds, related_services, related_adrs, key_concepts
   - Report any services missing this section or required fields

3. Verify ADR quick-reference.md coverage:
   - List all ADR files in /ADR/ (excluding template and quick-reference.md itself)
   - Compare to entries in /ADR/quick-reference.md
   - Report any ADRs not in the index
   - Verify each entry has: Status, Summary, Topics

4. Check ADR references in service frontmatter:
   - Extract ADR numbers mentioned in service `related_adrs:` fields
   - Verify these ADRs exist in /ADR/
   - Report any broken references

After auditing:
- Generate immediate guidance on how to fix these issues if the user wants to continue in this session. Be clear in this guidance so that the work can be immediately carried out by another agent.
- Perform this action on the repository using a subagent

Finally, provide:
- Summary of inconsistencies found (or confirmation if everything is consistent)
- Current counts: N core services, M add-ons, P ADRs
