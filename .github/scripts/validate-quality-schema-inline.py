#!/usr/bin/env python3
"""Fallback quality schema validator (used when schemas/quality-governance.schema.json is absent)."""
import json
import pathlib
import sys

path = ".claude/quality.json"
with pathlib.Path(path).open("r", encoding="utf-8") as f:
    data = json.load(f)
required = {
    "version", "project", "stacks", "coverage_threshold", "line_length",
    "test_pyramid", "traceability", "criticality_tier", "governance",
}
missing = sorted(required - set(data.keys()))
if missing:
    sys.exit(2)
gov = data.get("governance")
if not isinstance(gov, dict):
    sys.exit(2)
for k in (
    "delivery_model", "probabilistic", "reliability", "rolling_wave",
    "assurance_case", "privacy_preserving", "playbooks",
    "artifact_quality", "debt_registry", "onchain", "formal",
    "toolchains", "health",
):
    if k not in gov:
        sys.exit(2)
