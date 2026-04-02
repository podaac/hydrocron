#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
GENERATED_MD = ROOT / "docs" / "_generated_version.md"
GENERATED_SVG = ROOT / "docs" / "_generated_version.svg"


def read_version() -> str:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return data["tool"]["poetry"]["version"]


def build_badge_svg(version: str) -> str:
    label = "Version"
    label_width = 60
    value_width = max(60, 20 + len(version) * 7)
    total_width = label_width + value_width
    height = 20

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{height}" role="img" aria-label="{label}: {version}">
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#fff" stop-opacity=".7"/>
    <stop offset=".1" stop-color="#aaa" stop-opacity=".1"/>
    <stop offset=".9" stop-color="#000" stop-opacity=".3"/>
    <stop offset="1" stop-color="#000" stop-opacity=".5"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{total_width}" height="{height}" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="{height}" fill="#555"/>
    <rect x="{label_width}" width="{value_width}" height="{height}" fill="#007ec6"/>
    <rect width="{total_width}" height="{height}" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,DejaVu Sans,sans-serif" font-size="11">
    <text x="{label_width / 2}" y="14">{label}</text>
    <text x="{label_width + value_width / 2}" y="14">{version}</text>
  </g>
</svg>
"""


def write_generated(version: str) -> bool:
    md_content = "![Hydrocron version](_generated_version.svg)\n"
    svg_content = build_badge_svg(version)

    md_changed = True
    if GENERATED_MD.exists():
        current_md = GENERATED_MD.read_text(encoding="utf-8")
        md_changed = current_md != md_content

    svg_changed = True
    if GENERATED_SVG.exists():
        current_svg = GENERATED_SVG.read_text(encoding="utf-8")
        svg_changed = current_svg != svg_content

    if md_changed:
        GENERATED_MD.write_text(md_content, encoding="utf-8")
    if svg_changed:
        GENERATED_SVG.write_text(svg_content, encoding="utf-8")

    return md_changed or svg_changed


def main() -> None:
    version = read_version()
    changed = write_generated(version)
    if changed:
        print(f"Updated docs/_generated_version.* to version {version}")
    else:
        print(f"docs/_generated_version.* already at version {version}")


if __name__ == "__main__":
    main()
