#!/usr/bin/env python3
"""Render `cargo deny --format json` license check output as Markdown.

Used by the CI audit job to show license findings in the workflow summary.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def load_json_multi(path: Path) -> list[dict] | None:
    """Load one or more JSON objects from a file and return as list.

    Returns None if the file doesn't exist or is empty.
    Supports multiple top-level JSON objects concatenated in a stream.
    """
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return None

    decoder = json.JSONDecoder()
    idx = 0
    objs: list[dict] = []
    length = len(text)
    while idx < length:
        try:
            obj, offset = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            break
        objs.append(obj)
        idx += offset
        # skip whitespace/newlines between JSON objects
        while idx < length and text[idx].isspace():
            idx += 1

    return objs


def _traverse_graph(
    node: dict[str, Any], prefix: list[str] | None = None
) -> list[list[str]]:
    """Return all parent chains for a graph node as lists of "name@version".

    The node structure is expected to contain a `Krate` dict and optional `parents`.
    """
    if prefix is None:
        prefix = []
    kr = node.get("Krate", {})
    name = kr.get("name", "<unknown>")
    version = kr.get("version")
    part = f"{name}@{version}" if version else name
    new_prefix = prefix + [part]

    parents = node.get("parents") or []
    if not parents:
        return [new_prefix]

    chains: list[list[str]] = []
    for p in parents:
        chains.extend(_traverse_graph(p, new_prefix))
    return chains


def render(objs: list[dict] | None) -> tuple[str, int]:
    """Render cargo-deny JSON objects to Markdown and return (body, finding_count)."""
    lines = ["## Rust License Audit (cargo-deny)", ""]

    if objs is None:
        lines.append("_License check produced no output._")
        return "\n".join(lines), 0

    findings: list[dict] = []

    for obj in objs:
        if obj.get("type") != "diagnostic":
            continue
        fields = obj.get("fields", {})
        code = fields.get("code", "")
        # skip summary-like entries
        if code == "summary":
            continue
        findings.append(fields)

    if not findings:
        lines.append("✅ No license issues found.")
        return "\n".join(lines), 0

    total = len(findings)
    plural = "s" if total != 1 else ""
    lines.append(f"**{total} license issue{plural}** found.")
    lines.append("")

    lines.append("| Crate | Version | License | Reason | Trace |")
    lines.append("| --- | --- | --- | --- | --- |")

    for f in findings:
        # graphs may contain one or more graph entries describing the path
        graphs = f.get("graphs", [])
        message = f.get("message", "")
        severity = f.get("severity", "")
        labels = f.get("labels", [])
        license_span = ""
        for lab in labels:
            span = lab.get("span")
            if span:
                license_span = span
                break

        # For each graph produce a row per chain
        for g in graphs:
            # top-level krate for the graph
            kr = g.get("Krate", {})
            crate_name = kr.get("name", "<unknown>")
            crate_ver = kr.get("version", "")
            chains = _traverse_graph(g)
            # render each chain as left-to-right root->...->leaf
            for chain in chains:
                trace = " → ".join(chain)
                row = (
                    f"| `{crate_name}` | `{crate_ver}` | `{license_span}` "
                    f"| {message} ({severity}) | {trace} |"
                )
                lines.append(row)

    return "\n".join(lines), len(findings)


def write_github_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as fh:
            fh.write(f"{name}={value}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input", type=Path, help="Path to cargo deny --format json file"
    )
    parser.add_argument("output", type=Path, help="Path to output Markdown file")
    args = parser.parse_args()

    objs = load_json_multi(args.input)
    body, finding_count = render(objs)
    args.output.write_text(body + "\n", encoding="utf-8")

    has_findings = "true" if finding_count > 0 else "false"
    write_github_output("has_findings", has_findings)


if __name__ == "__main__":
    main()
