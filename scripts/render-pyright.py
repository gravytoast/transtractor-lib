"""Render pyright --outputjson output as Markdown.

Used by the CI typecheck job to show findings in the workflow summary.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

SRC_PREFIX = "/transtractor/"


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    text = path.read_text().strip()
    if not text:
        return None
    return json.loads(text)


def render(data: dict | None) -> str:
    lines = ["## Type checking (pyright)", ""]
    if data is None:
        lines.append("_pyright produced no output._")
        return "\n".join(lines)

    summary = data.get("summary", {})
    files_analyzed = summary.get("filesAnalyzed", 0)
    error_count = summary.get("errorCount", 0)

    diags = data.get("generalDiagnostics", [])
    errors = [d for d in diags if d.get("severity") == "error"]

    if not errors:
        lines.append(f"No type errors across {files_analyzed} files.")
        return "\n".join(lines)

    plural = "s" if error_count != 1 else ""
    lines.append(f"**{error_count} type error{plural}** across {files_analyzed} files.")
    lines.append("")

    by_rule = Counter(d.get("rule", "<no-rule>") for d in errors)
    by_file = Counter(d["file"].rsplit(SRC_PREFIX, 1)[-1] for d in errors)

    lines.append("Top error rules:")
    lines.append("")
    lines.append("| Count | Rule |")
    lines.append("| ---: | --- |")
    for rule, count in by_rule.most_common(10):
        lines.append(f"| {count} | `{rule}` |")
    lines.append("")
    lines.append("Top files:")
    lines.append("")
    lines.append("| Count | File |")
    lines.append("| ---: | --- |")
    for fname, count in by_file.most_common(10):
        lines.append(f"| {count} | `src/transtractor/{fname}` |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to pyright --outputjson file")
    parser.add_argument("output", type=Path, help="Path to output Markdown file")
    args = parser.parse_args()

    body = render(load_json(args.input))
    args.output.write_text(body + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
