#!/usr/bin/env python3
"""Render pip-audit JSON output as Markdown.

Used by the CI audit job to show Python vulnerability findings in the workflow summary.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def load_json(path: Path) -> list[dict[str, Any]] | None:
    """Load pip-audit JSON from a file and return a list of dependency records."""
    if not path.exists():
        return None

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return None

    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("dependencies", "results", "packages", "items"):
            value = data.get(key)
            if isinstance(value, list):
                return value

    return [data]


def _iter_vulnerabilities(dependencies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten dependency vulnerability entries into a single list."""
    findings: list[dict[str, Any]] = []

    for dep in dependencies:
        if not isinstance(dep, dict):
            continue

        name = (
            dep.get("name")
            or dep.get("package")
            or dep.get("package_name")
            or "unknown"
        )
        version = dep.get("version") or dep.get("release") or ""
        vulns = dep.get("vulns") or dep.get("vulnerabilities") or []

        if not isinstance(vulns, list):
            continue

        for vuln in vulns:
            if not isinstance(vuln, dict):
                continue
            finding = {
                "name": name,
                "version": version,
                "id": vuln.get("id") or vuln.get("vuln_id") or "N/A",
                "fix_versions": vuln.get("fix_versions")
                or vuln.get("fix_versions")
                or [],
                "description": vuln.get("description") or vuln.get("summary") or "N/A",
            }
            findings.append(finding)

    return findings


def render(data: list[dict[str, Any]] | dict[str, Any] | None) -> tuple[str, int]:
    """Render pip-audit JSON data as Markdown and return (body, finding_count)."""
    lines = ["## Python Dependency Audit (pip-audit)", ""]

    if data is None:
        lines.append("_Audit produced no output._")
        return "\n".join(lines), 0

    dependencies = data if isinstance(data, list) else [data]
    if isinstance(data, dict):
        for key in ("dependencies", "results", "packages", "items"):
            value = data.get(key)
            if isinstance(value, list):
                dependencies = value
                break

    findings = _iter_vulnerabilities(dependencies)

    if not findings:
        lines.append("✅ No known vulnerabilities found.")
        return "\n".join(lines), 0

    total = len(findings)
    plural = "s" if total != 1 else ""
    lines.append(f"**{total} known vulnerability{plural}** found.")
    lines.append("")
    lines.append("### Findings")
    lines.append("")
    lines.append("| Package | Version | ID | Fix Versions | Summary |")
    lines.append("| --- | --- | --- | --- | --- |")

    for finding in findings:
        package = finding.get("name", "unknown")
        version = finding.get("version") or ""
        vuln_id = finding.get("id", "N/A")
        fix_versions = ", ".join(str(v) for v in finding.get("fix_versions", []) or [])
        if not fix_versions:
            fix_versions = "N/A"
        description = str(finding.get("description", "N/A"))
        lines.append(
            f"| `{package}` | `{version}` | `{vuln_id}` "
            f"| `{fix_versions}` | {description} |"
        )

    return "\n".join(lines), len(findings)


def write_github_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as fh:
            fh.write(f"{name}={value}\n")


def main() -> None:
    """Parse arguments and render pip-audit output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to pip-audit JSON file")
    parser.add_argument("output", type=Path, help="Path to output Markdown file")
    args = parser.parse_args()

    body, finding_count = render(load_json(args.input))
    args.output.write_text(body + "\n", encoding="utf-8")

    has_findings = "true" if finding_count > 0 else "false"
    write_github_output("has_findings", has_findings)


if __name__ == "__main__":
    main()
