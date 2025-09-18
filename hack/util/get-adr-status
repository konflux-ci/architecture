#!/bin/bash

# get-adr-status.sh - Extract status from ADR markdown files
#
# Usage: ./get-adr-status.sh <adr-file>
#
# This script extracts the status from an ADR markdown file.
# The status is the first word that appears in the ## Status section.
#
# Exit codes:
#   0 - Success, status found and printed
#   1 - Error: file not found or not readable
#   2 - Error: no ## Status section found
#   3 - Error: status section is empty

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print error messages
error() {
    echo -e "${RED}ERROR:${NC} $1" >&2
}

# Function to print usage
usage() {
    echo "Usage: $0 <adr-file>"
    echo ""
    echo "Extract the status from an ADR markdown file."
    echo "The status is the first word that appears in the ## Status section."
    echo ""
    echo "Arguments:"
    echo "  adr-file    Path to the ADR markdown file"
    echo ""
    echo "Exit codes:"
    echo "  0  Success, status found and printed"
    echo "  1  Error: file not found or not readable"
    echo "  2  Error: no ## Status section found"
    echo "  3  Error: status section is empty"
    echo ""
    echo "Examples:"
    echo "  $0 ADR/0000-adr-template.md"
    echo "  $0 ADR/0001-pipeline-service-phase-1.md"
}

# Check if help is requested
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

# Check if file argument is provided
if [[ $# -ne 1 ]]; then
    error "Exactly one argument (ADR file path) is required"
    echo ""
    usage
    exit 1
fi

adr_file="$1"

# Check if file exists and is readable
if [[ ! -f "$adr_file" ]]; then
    error "File '$adr_file' not found"
    exit 1
fi

if [[ ! -r "$adr_file" ]]; then
    error "File '$adr_file' is not readable"
    exit 1
fi

# Check if file has .md extension (optional but good practice)
if [[ ! "$adr_file" =~ \.md$ ]]; then
    echo -e "${YELLOW}Warning:${NC} File '$adr_file' doesn't have .md extension" >&2
fi

# Extract the status section and get the first word
# We look for lines starting with ## Status and capture the next non-empty line
status_line=$(awk '
    /^## Status$/ {
        # Found Status section header
        in_status = 1
        next
    }
    in_status && /^##/ {
        # Hit next section, stop looking
        in_status = 0
        next
    }
    in_status && /^[[:space:]]*$/ {
        # Skip empty lines
        next
    }
    in_status {
        # Found first non-empty line in Status section
        print $0
        exit
    }
' "$adr_file")

# Check if we found a status section
if [[ -z "$status_line" ]]; then
    error "No ## Status section found in '$adr_file'"
    exit 2
fi

# Extract the first word from the status line
# Remove any markdown formatting (**, _, etc.) and get first word
status=$(echo "$status_line" | sed 's/[*_`]//g' | awk '{print $1}')

# Check if status is empty after processing
if [[ -z "$status" ]]; then
    error "Status section is empty or contains only formatting in '$adr_file'"
    exit 3
fi

# Print the status (just the word, no extra formatting)
echo "$status" 