"""Give the staged pages the front matter descriptions llms.txt should quote.

Sourcey summarizes a page from its first paragraph, which for an ADR is the
date/status preamble ("Date: 2022-06-17", "Accepted") rather than anything about
the decision. Setting a `description` in front matter overrides that, so this
step rewrites the *staged copies* only - the repository's own markdown is never
touched - with:

  ADR/<n>-*.md  -> the first sentence of the ADR's "## Context" (or
                   "## Context and Problem Statement") section.
  index.md      -> SITE_SUMMARY, which Sourcey also reuses as the one-line
                   site summary at the top of llms.txt.

Deterministic and rule-based: same input tree, same descriptions.

Usage: python inject_descriptions.py <stage_dir>
"""
import json
import re
import sys
from pathlib import Path

SITE_SUMMARY = (
    "Technical and architecture documentation for Konflux, an open source CI/CD "
    "system: a platform overview, the core and add-on services it is built from, "
    "and the architecture decision records (ADRs) behind them."
)

FRONT_MATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*\r?\n", re.DOTALL)
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
CONTEXT = re.compile(r"^Context\b", re.IGNORECASE)
BOLD_LABEL = re.compile(r"\A\*\*[^*]+\*\*:?\Z")
LIST_MARKER = re.compile(r"\A(?:[-*+]|\d+\.)\s+")
COMMENT = re.compile(r"\A(?:<!--|\[//\]: #)")
# Markdown links, in the three spellings used across the ADRs, reduced to their
# visible label (Sourcey does the same to the descriptions it derives itself).
LINKS = (
    (re.compile(r"!?\[([^\]]*)\]\([^)]*\)"), r"\1"),
    (re.compile(r"\[([^\]]+)\]\[[^\]]*\]"), r"\1"),
    (re.compile(r"(?<![\w`])\[([^\]]+)\]"), r"\1"),
)
# Abbreviations that end in a period without ending a sentence.
ABBREVIATIONS = ("e.g", "i.e", "etc", "vs", "cf", "al", "resp", "approx", "no",
                 "fig", "sec", "ch", "mr", "mrs", "ms", "dr", "inc", "ltd")
SENTENCE_END = re.compile(r"[.!?](?=\s)")


def strip_front_matter(text: str):
    """Split a page into (front matter block, body). Body is "" if unparsable."""
    match = FRONT_MATTER.match(text)
    if not match:
        return "", text
    return match.group(0), text[match.end():]


def context_paragraph(body: str) -> str:
    """The first prose paragraph of the "## Context" section, as one line."""
    lines = body.splitlines()
    start = None
    for i, line in enumerate(lines):
        heading = HEADING.match(line)
        if heading and CONTEXT.match(heading.group(2).strip()):
            start, level = i + 1, len(heading.group(1))
            break
    if start is None:
        return ""

    paragraph = []
    for line in lines[start:]:
        stripped = line.strip()
        heading = HEADING.match(stripped)
        if heading:
            if len(heading.group(1)) <= level:
                break  # left the Context section
            continue  # a sub-heading inside it; the prose follows
        if not stripped or COMMENT.match(stripped):
            if paragraph:
                break
            continue
        stripped = stripped.lstrip("> ").strip()
        if not paragraph:
            if BOLD_LABEL.match(stripped):
                continue  # a "**Problem**" style label on its own line
            stripped = LIST_MARKER.sub("", stripped)
        paragraph.append(stripped)
    return " ".join(paragraph)


def first_sentence(paragraph: str) -> str:
    for pattern, replacement in LINKS:
        paragraph = pattern.sub(replacement, paragraph)
    text = re.sub(r"\s+", " ", paragraph).strip()
    for match in SENTENCE_END.finditer(text):
        word = re.split(r"[\s(]", text[:match.start()])[-1].lower()
        if word.rstrip(".") in ABBREVIATIONS or len(word.rstrip(".")) < 2:
            continue  # "e.g. foo", "J. Doe": not a sentence boundary
        return text[:match.start() + 1]
    # A paragraph that only introduces a list ends in a colon; close it off.
    return text[:-1] + "." if text.endswith(":") else text


def describe(page: Path) -> str:
    front_matter, body = strip_front_matter(page.read_text(encoding="utf-8"))
    if not front_matter:
        return ""
    return first_sentence(context_paragraph(body))


def set_description(page: Path, description: str) -> None:
    """Add `description` to the staged page's front matter (replacing any)."""
    front_matter, body = strip_front_matter(page.read_text(encoding="utf-8"))
    if not front_matter or not description:
        return
    kept = [line for line in front_matter.splitlines()[1:-1]
            if not line.startswith("description:")]
    kept.append("description: " + json.dumps(description, ensure_ascii=False))
    page.write_text("---\n" + "\n".join(kept) + "\n---\n" + body,
                    encoding="utf-8", newline="\n")


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: inject_descriptions.py <stage_dir>")
    stage = Path(sys.argv[1])
    if not (stage / "ADR").is_dir():
        sys.exit(f"error: {stage} does not look like a staged tree (no ADR/)")

    described = 0
    for page in sorted((stage / "ADR").glob("*.md")):
        description = describe(page)
        if description:
            set_description(page, description)
            described += 1
    set_description(stage / "index.md", SITE_SUMMARY)
    print(f"described {described} ADRs in {stage}")


if __name__ == "__main__":
    main()
