"""
Run Reducto extract on parsed documents using a given schema version.

Usage:
    python extract.py              # defaults to v1
    python extract.py v2           # run with schemas/v2/schema.json
"""

import csv
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from reducto import Reducto

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")


def load_job_ids() -> list[dict]:
    with open(ROOT / "job_ids.csv") as f:
        return list(csv.DictReader(f))


def run_extract(version: str = "v1"):
    schema_dir = ROOT / "schemas" / version
    schema_path = schema_dir / "schema.json"

    if not schema_path.exists():
        print(f"Schema not found: {schema_path}")
        sys.exit(1)

    with open(schema_path) as f:
        schema = json.load(f)

    # Load optional system prompt
    system_prompt = None
    prompt_path = schema_dir / "system_prompt.txt"
    if prompt_path.exists():
        system_prompt = prompt_path.read_text().strip()

    # Load optional settings
    settings = {}
    settings_path = schema_dir / "settings.json"
    if settings_path.exists():
        with open(settings_path) as f:
            settings = json.load(f)

    jobs = load_job_ids()
    client = Reducto()

    for job in jobs:
        filename = job["filename"]
        job_id = job["job_id"]
        print(f"\n{'='*60}")
        print(f"Extracting: {filename}")
        print(f"Job ID:     {job_id}")
        print(f"Schema:     {version}")
        if system_prompt:
            print(f"Prompt:     {system_prompt[:80]}...")
        if settings:
            print(f"Settings:   {settings}")
        print(f"{'='*60}")

        instructions = {"schema": schema}
        if system_prompt:
            instructions["system_prompt"] = system_prompt

        kwargs = dict(input=f"jobid://{job_id}", instructions=instructions)
        if settings:
            kwargs["settings"] = settings

        result = client.extract.run(**kwargs)

        data = result.result[0] if result.result else {}

        # Compute derived fields from raw values
        data = compute_derived_fields(data)

        # Save JSON output
        out_name = filename.replace(".pdf", f".{version}.extract.json")
        out_path = schema_dir / out_name
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Saved: {out_path.relative_to(ROOT)}")

    # Generate comparison report
    generate_report(version, schema_dir, jobs)


def compute_derived_fields(data: dict) -> dict:
    """Compute fields that Reducto docs recommend calculating in code."""
    cf = data.get("cash_flow", {})
    capex = data.get("capex", {})

    # Free cash flow = operating cash flow - capex
    op_cf = cf.get("operating_cash_flow")
    pp_e = capex.get("total_capex")
    if op_cf and pp_e and not cf.get("free_cash_flow"):
        cf["free_cash_flow"] = op_cf - pp_e

    return data


def _is_present(v):
    """Return True if a value represents real extracted data."""
    if v is None or v == "" or v is False:
        return False
    if isinstance(v, (int, float)) and v == 0:
        return False
    return True


def _format_value(k, v):
    """Format a value for the report. Numbers get commas, pcts stay as-is."""
    if isinstance(v, float):
        if "pct" in k or "growth" in k or "margin" in k or "mix" in k:
            return f"{v:.2f}%"
        return f"{v:,.2f}"
    if isinstance(v, int):
        return f"{v:,}"
    return str(v)


def _render_dict(data: dict, indent: int, lines: list, skip_keys=None):
    """Recursively render a dict, omitting empty/null/zero values."""
    prefix = " " * indent
    skip = skip_keys or set()
    for k, v in data.items():
        if k in skip:
            continue
        if isinstance(v, dict):
            # Check if the nested dict has any present values
            if any(_is_present(sv) for sv in v.values() if not isinstance(sv, (dict, list))):
                lines.append(f"{prefix}{k}:")
                _render_dict(v, indent + 2, lines)
        elif isinstance(v, list):
            non_empty = [item for item in v if isinstance(item, dict) and any(_is_present(sv) for sv in item.values())]
            if non_empty:
                lines.append(f"{prefix}{k}:")
                for item in non_empty:
                    label = item.get("segment_name") or item.get("metric_name") or ""
                    if label:
                        lines.append(f"{prefix}  -- {label} --")
                    _render_dict(item, indent + 4, lines, skip_keys={"segment_name", "metric_name"})
        elif isinstance(v, bool):
            lines.append(f"{prefix}{k}: {'Yes' if v else 'No'}")
        elif _is_present(v):
            lines.append(f"{prefix}{k}: {_format_value(k, v)}")


def generate_report(version: str, schema_dir: Path, jobs: list[dict]):
    """Write a facts-only report — omit missing/null fields, no commentary."""
    report_lines = [f"Extraction Report — {version}", "=" * 60, ""]

    for job in jobs:
        filename = job["filename"]
        out_name = filename.replace(".pdf", f".{version}.extract.json")
        out_path = schema_dir / out_name

        report_lines.append(f"{'='*60}")
        report_lines.append(f"  {filename}")
        report_lines.append(f"{'='*60}")

        if not out_path.exists():
            report_lines.append("  No extraction output.\n")
            continue

        with open(out_path) as f:
            data = json.load(f)

        _render_dict(data, 2, report_lines)
        report_lines.append("")

    report = "\n".join(report_lines)
    report_path = schema_dir / "report.txt"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport: {report_path.relative_to(ROOT)}")


if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "v1"
    run_extract(version)
