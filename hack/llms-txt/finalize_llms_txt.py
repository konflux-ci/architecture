"""Turn the Sourcey-emitted llms.txt into the file this site publishes.

Two deterministic, rule-based passes; page content is never edited.

1. URLs. Sourcey emits `.html`-suffixed, lowercased paths; the live Eleventy site
   serves clean trailing-slash URLs and keeps the `ADR/` directory uppercase.
   URLs are also absolutized against the site origin so the index is consumable
   away from the site root (MCP docs servers). Rules (in order), applied only to
   site-internal markdown link targets (external links and bare anchors are left
   untouched; URL fragments are preserved):
     1. leading `/architecture/adr/`  -> `/architecture/ADR/`
     2. trailing `.html`              -> `/`
     3. ADR slug case restored from the repository tree (e.g. `...-gcl-...` -> `...-GCL-...`)
     4. leading `/`                   -> `https://konflux-ci.dev/`

2. Sections. Sourcey lists every page flat under its single navigation tab, but
   llms.txt readers expect H2 sections. Entries are regrouped under the same
   groups the Sourcey config is built from (Overview, Core Services, Add-ons,
   ADRs); eleventy_nav_to_sourcey.slugs_for stays the one source of that grouping.

Usage: python finalize_llms_txt.py <in> <out> <repo_root>
"""
import re
import sys
from pathlib import Path

from eleventy_nav_to_sourcey import slugs_for

ORIGIN = "https://konflux-ci.dev"
BASE_URL = "/architecture"
ENTRY = re.compile(r"^- \[[^\]]*\]\((?P<url>[^)]+)\)")


def true_case_map(repo: Path) -> dict:
    """lowercase ADR slug -> true-case slug, from the repository tree (deterministic)."""
    out = {}
    for f in (repo / "ADR").glob("*.md"):
        slug = f.name[:-3]
        out[slug.lower()] = slug
    return out


def normalize(text: str, cases: dict) -> str:
    def fix(m):
        url = m.group(2)
        if not url.startswith("/"):
            return m.group(0)  # external links and anchors are left untouched
        path, sep, frag = url.partition("#")
        if path.startswith("/architecture/adr/"):
            path = "/architecture/ADR/" + path[len("/architecture/adr/"):]
        if path.endswith(".html"):
            path = path[:-len(".html")] + "/"
        adr = re.match(r"^/architecture/ADR/([^/]+)/$", path)
        if adr and adr.group(1).lower() in cases:
            path = f"/architecture/ADR/{cases[adr.group(1).lower()]}/"
        return f"[{m.group(1)}]({ORIGIN}{path}{sep}{frag})"

    return re.sub(r"\[([^\]]*)\]\(([^)]+)\)", fix, text)


def path_of(url: str) -> str:
    """The site path an entry URL points at, relative to the base URL."""
    path = url.partition("#")[0]
    prefix = f"{ORIGIN}{BASE_URL}/"
    return path[len(prefix):].strip("/") if path.startswith(prefix) else url


def path_of_slug(slug: str) -> str:
    """The same path for a config slug: an `index` page is served as its directory."""
    if slug == "index":
        return ""
    return slug[:-len("/index")] if slug.endswith("/index") else slug


def regroup(text: str, groups: list) -> str:
    """Re-emit the flat entry list under one H2 heading per navigation group."""
    entries, preamble = {}, []
    for line in text.splitlines():
        entry = ENTRY.match(line)
        if entry:
            entries[path_of(entry.group("url"))] = line
        elif not line.startswith("## "):
            preamble.append(line.rstrip())

    out = preamble
    while out and not out[-1]:
        out.pop()
    for group in groups:
        paths = [path_of_slug(slug) for slug in group["pages"]]
        listed = [entries.pop(path) for path in paths if path in entries]
        if listed:
            out += ["", f"## {group['group']}", ""] + listed
    if entries:
        sys.exit(f"error: entries outside every navigation group: {sorted(entries)}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("usage: finalize_llms_txt.py <in> <out> <repo_root>")
    src, dst, repo = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    if not (repo / "ADR").is_dir():
        sys.exit(f"error: {repo} does not look like the repo root (no ADR/ directory)")
    text = normalize(src.read_text(encoding="utf-8"), true_case_map(repo))
    dst.write_text(regroup(text, slugs_for(repo)), encoding="utf-8", newline="\n")
    print(f"finalized {src} -> {dst}")
