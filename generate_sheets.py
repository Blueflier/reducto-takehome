"""
Generate CSVs from extraction JSON for Google Sheets upload.

Usage:
    python generate_sheets.py v8

Outputs to sheets/<version>/ with one CSV per tab.
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def load_data(version: str) -> dict:
    """Load extraction JSONs keyed by company label."""
    schema_dir = ROOT / "schemas" / version
    companies = {}
    for path in sorted(schema_dir.glob("*.extract.json")):
        # Derive label from filename
        name = path.name.replace(f".{version}.extract.json", "")
        if "AMZN" in name:
            label = "Amazon"
            period = "Q4 2024 / FY 2024"
        elif "10-Q" in name:
            label = "Apple"
            period = "Q3 2024 / 9M 2024"
        else:
            label = name
            period = ""
        with open(path) as f:
            companies[label] = {"data": json.load(f), "period": period}
    return companies


def fmt(v, pct=False):
    """Format a value for CSV."""
    if v is None:
        return ""
    if pct and isinstance(v, (int, float)):
        return f"{v:.2f}%"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def write_csv(path: Path, rows: list[list]):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"  {path.name}")


def generate_financials(companies: dict, out_dir: Path):
    labels = list(companies.keys())
    header = ["Metric (in $M except per-share)"] + [f"{l} ({companies[l]['period']})" for l in labels]

    def row(name, section, key, pct=False):
        vals = [name]
        for l in labels:
            v = companies[l]["data"].get(section, {}).get(key)
            vals.append(fmt(v, pct=pct))
        return vals

    rows = [
        header,
        [],
        ["NET SALES"],
        row("Quarterly Net Sales", "total_net_sales", "quarterly_sales"),
        row("Prior Year Quarter", "total_net_sales", "quarterly_prior_year_sales"),
        row("Quarterly YoY Growth", "total_net_sales", "quarterly_growth_pct", pct=True),
        row("Full Year Net Sales", "total_net_sales", "full_year_sales"),
        row("Prior Full Year", "total_net_sales", "full_year_prior_year_sales"),
        row("Full Year YoY Growth", "total_net_sales", "full_year_growth_pct", pct=True),
        [],
        ["OPERATING INCOME"],
        row("Quarterly Operating Income", "operating_income", "quarterly_operating_income"),
        row("Quarterly Operating Margin", "operating_income", "quarterly_operating_margin_pct", pct=True),
        row("Full Year Operating Income", "operating_income", "full_year_operating_income"),
        row("Full Year Operating Margin", "operating_income", "full_year_operating_margin_pct", pct=True),
        [],
        ["NET INCOME & EPS"],
        row("Quarterly Net Income", "net_income_and_eps", "quarterly_net_income"),
        row("Quarterly EPS (Basic)", "net_income_and_eps", "quarterly_eps_basic"),
        row("Quarterly EPS (Diluted)", "net_income_and_eps", "quarterly_eps_diluted"),
        row("Full Year Net Income", "net_income_and_eps", "full_year_net_income"),
        row("Full Year EPS (Basic)", "net_income_and_eps", "full_year_eps_basic"),
        row("Full Year EPS (Diluted)", "net_income_and_eps", "full_year_eps_diluted"),
        [],
        ["CASH FLOW"],
        row("Operating Cash Flow", "cash_flow", "operating_cash_flow"),
        row("Free Cash Flow", "cash_flow", "free_cash_flow"),
        row("CapEx (PP&E Purchases)", "capex", "total_capex"),
    ]

    write_csv(out_dir / "financials.csv", rows)


def generate_segments(companies: dict, out_dir: Path):
    rows = []

    for label, info in companies.items():
        period = info["period"]
        segments = info["data"].get("segments", [])
        if not segments:
            continue

        rows.append([f"{label} Segments ({period})"])
        rows.append(["Segment", "Net Sales ($M)", "Prior Year ($M)", "YoY Growth", "Op Income ($M)", "Op Margin", "Revenue Mix"])

        for seg in segments:
            rows.append([
                seg.get("segment_name", ""),
                fmt(seg.get("quarterly_net_sales")),
                fmt(seg.get("quarterly_prior_year_net_sales")),
                fmt(seg.get("quarterly_yoy_growth_pct"), pct=True),
                fmt(seg.get("quarterly_operating_income")),
                fmt(seg.get("quarterly_operating_margin_pct"), pct=True),
                fmt(seg.get("revenue_mix_pct"), pct=True),
            ])

        rows.append([])

    write_csv(out_dir / "segments.csv", rows)


def generate_cash_flow(companies: dict, out_dir: Path):
    labels = list(companies.keys())
    header = ["Metric ($M)"] + [f"{l} ({companies[l]['period']})" for l in labels]

    def row(name, *keys):
        vals = [name]
        for l in labels:
            d = companies[l]["data"]
            v = d
            for k in keys:
                v = v.get(k, {}) if isinstance(v, dict) else None
            if v is None or v == 0 or isinstance(v, dict):
                vals.append("")
            else:
                vals.append(fmt(v))
        return vals

    rows = [
        header,
        [],
        ["CAPITAL EXPENDITURES"],
        row("Purchases of PP&E", "cash_flow_and_liquidity", "capital_expenditures", "purchases_of_property_and_equipment"),
        row("Finance Lease Additions", "cash_flow_and_liquidity", "capital_expenditures", "finance_lease_additions"),
        row("Proceeds from Asset Sales", "cash_flow_and_liquidity", "capital_expenditures", "proceeds_from_asset_sales"),
        [],
        ["DEBT SERVICE"],
        row("Long-Term Debt Repayments", "cash_flow_and_liquidity", "debt_repayments", "long_term_debt_repayments"),
        row("Short-Term Debt Repayments", "cash_flow_and_liquidity", "debt_repayments", "short_term_debt_repayments"),
        [],
        ["LEASE OBLIGATIONS"],
        row("Finance Lease Repayments", "cash_flow_and_liquidity", "lease_obligations", "finance_lease_principal_repayments"),
        row("Operating Lease Payments", "cash_flow_and_liquidity", "lease_obligations", "operating_lease_payments"),
        [],
        ["LIQUIDITY"],
        row("Cash & Equivalents", "cash_flow_and_liquidity", "liquidity", "cash_and_equivalents"),
        row("Current Marketable Securities", "cash_flow_and_liquidity", "liquidity", "current_marketable_securities"),
        row("Non-Current Marketable Securities", "cash_flow_and_liquidity", "liquidity", "non_current_marketable_securities"),
        row("Total Debt", "cash_flow_and_liquidity", "liquidity", "total_debt"),
    ]

    # Add computed totals
    total_cash_row = ["Total Cash & Securities"]
    for l in labels:
        liq = companies[l]["data"].get("cash_flow_and_liquidity", {}).get("liquidity", {})
        total = (liq.get("cash_and_equivalents", 0) or 0) + \
                (liq.get("current_marketable_securities", 0) or 0) + \
                (liq.get("non_current_marketable_securities", 0) or 0)
        total_cash_row.append(fmt(total) if total else "")
    rows.append(total_cash_row)

    net_cash_row = ["Net Cash (Cash & Securities - Debt)"]
    for l in labels:
        liq = companies[l]["data"].get("cash_flow_and_liquidity", {}).get("liquidity", {})
        total_cash = (liq.get("cash_and_equivalents", 0) or 0) + \
                     (liq.get("current_marketable_securities", 0) or 0) + \
                     (liq.get("non_current_marketable_securities", 0) or 0)
        debt = liq.get("total_debt", 0) or 0
        net = total_cash - debt
        net_cash_row.append(fmt(net) if total_cash else "")
    rows.append(net_cash_row)

    write_csv(out_dir / "cash_flow.csv", rows)


def generate_guidance(companies: dict, out_dir: Path):
    labels = list(companies.keys())
    header = ["Metric"] + [f"{l}" for l in labels]

    rows = [
        header,
        [],
        ["FORWARD GUIDANCE"],
    ]

    def row(name, key, pct=False):
        vals = [name]
        for l in labels:
            fg = companies[l]["data"].get("forward_guidance", {})
            if not fg.get("has_guidance"):
                vals.append("Not provided")
            else:
                v = fg.get(key)
                vals.append(fmt(v, pct=pct) if v is not None else "")
        return vals

    rows.extend([
        row("Guidance Period", "guidance_period"),
        row("Revenue Low ($M)", "revenue_low"),
        row("Revenue High ($M)", "revenue_high"),
        row("Revenue Growth Low", "revenue_growth_low_pct", pct=True),
        row("Revenue Growth High", "revenue_growth_high_pct", pct=True),
        row("Operating Income Low ($M)", "operating_income_low"),
        row("Operating Income High ($M)", "operating_income_high"),
        [],
        ["FX IMPACT"],
        row("FX Impact ($M)", "fx_impact_amount"),
        row("FX Impact (bps)", "fx_impact_bps"),
    ])

    write_csv(out_dir / "guidance.csv", rows)


def generate_notes(companies: dict, out_dir: Path):
    labels = list(companies.keys())
    header = ["Metric"] + [f"{l} ({companies[l]['period']})" for l in labels]

    rows = [
        header,
        [],
        ["STOCK-BASED COMPENSATION ($M)"],
    ]

    def sbc_row(name, key):
        vals = [name]
        for l in labels:
            v = companies[l]["data"].get("key_business_metrics", {}).get("stock_based_compensation", {}).get(key)
            vals.append(fmt(v) if v else "")
        return vals

    rows.extend([
        sbc_row("Quarterly SBC", "quarterly_sbc"),
        sbc_row("Prior Year Quarter SBC", "quarterly_prior_year_sbc"),
        sbc_row("Full Year SBC", "full_year_sbc"),
        sbc_row("Prior Full Year SBC", "full_year_prior_year_sbc"),
        [],
        ["OPERATIONAL KPIs"],
    ])

    # KPIs vary by company — list them per company
    for label, info in companies.items():
        kpis = info["data"].get("key_business_metrics", {}).get("operational_kpis", [])
        if kpis:
            rows.append([f"{label} KPIs"])
            rows.append(["Metric", "Current Value", "YoY Change"])
            for kpi in kpis:
                rows.append([
                    kpi.get("metric_name", ""),
                    kpi.get("current_value", ""),
                    kpi.get("yoy_change", ""),
                ])
            rows.append([])

    rows.append(["ASSUMPTIONS & ADJUSTMENTS"])
    rows.append(["", "All monetary values in $M unless noted"])
    rows.append(["", "Free cash flow = Operating Cash Flow - CapEx (computed, not extracted) for companies that do not report it directly"])
    rows.append(["", "Growth percentages calculated from table values: (current - prior) / prior * 100"])
    rows.append(["", "Apple does not provide forward guidance"])

    write_csv(out_dir / "notes.csv", rows)


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "v8"
    out_dir = ROOT / "sheets" / version
    out_dir.mkdir(parents=True, exist_ok=True)

    companies = load_data(version)
    print(f"Generating CSVs for {version} → sheets/{version}/")

    generate_financials(companies, out_dir)
    generate_segments(companies, out_dir)
    generate_cash_flow(companies, out_dir)
    generate_guidance(companies, out_dir)
    generate_notes(companies, out_dir)

    print(f"\nDone. Upload these 5 CSVs to Google Sheets as separate tabs.")


if __name__ == "__main__":
    main()
