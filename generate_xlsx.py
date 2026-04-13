"""
Generate a formatted .xlsx with native Excel charts from extraction JSON.

Usage:
    python generate_xlsx.py v8

Outputs to sheets/<version>/report.xlsx
"""

import json
import sys
from pathlib import Path

import xlsxwriter

ROOT = Path(__file__).parent

AMZN_COLOR = "#FF9900"
AAPL_COLOR = "#555555"
HEADER_BG = "#1F4E79"
SECTION_BG = "#D6E4F0"
ALT_ROW_BG = "#F2F7FB"


def load_data(version: str) -> dict:
    schema_dir = ROOT / "schemas" / version
    companies = {}
    for path in sorted(schema_dir.glob("*.extract.json")):
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


def make_formats(wb):
    """Create reusable cell formats."""
    f = {}
    f["header"] = wb.add_format({
        "bold": True, "font_color": "white", "bg_color": HEADER_BG,
        "border": 1, "font_size": 11, "align": "center",
    })
    f["section"] = wb.add_format({
        "bold": True, "bg_color": SECTION_BG, "border": 1, "font_size": 11,
    })
    f["label"] = wb.add_format({"border": 1, "font_size": 10, "indent": 1})
    f["num"] = wb.add_format({"border": 1, "font_size": 10, "num_format": "#,##0", "align": "right"})
    f["pct"] = wb.add_format({"border": 1, "font_size": 10, "num_format": "0.00%", "align": "right"})
    f["dollar"] = wb.add_format({"border": 1, "font_size": 10, "num_format": "$#,##0.00", "align": "right"})
    f["text"] = wb.add_format({"border": 1, "font_size": 10, "text_wrap": True})
    f["text_center"] = wb.add_format({"border": 1, "font_size": 10, "align": "center"})
    f["alt_num"] = wb.add_format({"border": 1, "font_size": 10, "num_format": "#,##0", "align": "right", "bg_color": ALT_ROW_BG})
    f["alt_pct"] = wb.add_format({"border": 1, "font_size": 10, "num_format": "0.00%", "align": "right", "bg_color": ALT_ROW_BG})
    f["alt_dollar"] = wb.add_format({"border": 1, "font_size": 10, "num_format": "$#,##0.00", "align": "right", "bg_color": ALT_ROW_BG})
    f["alt_label"] = wb.add_format({"border": 1, "font_size": 10, "indent": 1, "bg_color": ALT_ROW_BG})
    return f


def write_row(ws, row, label, vals, fmt_label, fmt_val):
    """Write a label + value cells."""
    ws.write(row, 0, label, fmt_label)
    for i, v in enumerate(vals):
        if v is not None:
            ws.write(row, 1 + i, v, fmt_val)


def build_financials(wb, companies, fmts):
    ws = wb.add_worksheet("Financials")
    labels = list(companies.keys())
    ws.set_column(0, 0, 32)
    ws.set_column(1, len(labels), 30)

    # Header
    r = 0
    ws.write(r, 0, "Metric (in $M except per-share)", fmts["header"])
    for i, l in enumerate(labels):
        ws.write(r, 1 + i, f"{l} ({companies[l]['period']})", fmts["header"])

    def get(label, section, key):
        return companies[label]["data"].get(section, {}).get(key)

    def data_row(row, name, section, key, fmt_type="num"):
        alt = (row % 2 == 0)
        fl = fmts["alt_label"] if alt else fmts["label"]
        fv = fmts[f"alt_{fmt_type}"] if alt else fmts[fmt_type]
        ws.write(row, 0, name, fl)
        for i, l in enumerate(labels):
            v = get(l, section, key)
            if v is not None:
                if fmt_type == "pct":
                    v = v / 100
                ws.write(row, 1 + i, v, fv)

    # Net Sales
    r = 2
    ws.merge_range(r, 0, r, len(labels), "NET SALES", fmts["section"])
    r = 3; data_row(r, "Quarterly Net Sales", "total_net_sales", "quarterly_sales")
    r = 4; data_row(r, "Prior Year Quarter", "total_net_sales", "quarterly_prior_year_sales")
    r = 5; data_row(r, "Quarterly YoY Growth", "total_net_sales", "quarterly_growth_pct", "pct")
    r = 6; data_row(r, "Full Year Net Sales", "total_net_sales", "full_year_sales")
    r = 7; data_row(r, "Prior Full Year", "total_net_sales", "full_year_prior_year_sales")
    r = 8; data_row(r, "Full Year YoY Growth", "total_net_sales", "full_year_growth_pct", "pct")

    # Operating Income
    r = 10
    ws.merge_range(r, 0, r, len(labels), "OPERATING INCOME", fmts["section"])
    r = 11; data_row(r, "Quarterly Operating Income", "operating_income", "quarterly_operating_income")
    r = 12; data_row(r, "Quarterly Operating Margin", "operating_income", "quarterly_operating_margin_pct", "pct")
    r = 13; data_row(r, "Full Year Operating Income", "operating_income", "full_year_operating_income")
    r = 14; data_row(r, "Full Year Operating Margin", "operating_income", "full_year_operating_margin_pct", "pct")

    # Net Income & EPS
    r = 16
    ws.merge_range(r, 0, r, len(labels), "NET INCOME & EPS", fmts["section"])
    r = 17; data_row(r, "Quarterly Net Income", "net_income_and_eps", "quarterly_net_income")
    r = 18; data_row(r, "Quarterly EPS (Basic)", "net_income_and_eps", "quarterly_eps_basic", "dollar")
    r = 19; data_row(r, "Quarterly EPS (Diluted)", "net_income_and_eps", "quarterly_eps_diluted", "dollar")
    r = 20; data_row(r, "Full Year Net Income", "net_income_and_eps", "full_year_net_income")
    r = 21; data_row(r, "Full Year EPS (Basic)", "net_income_and_eps", "full_year_eps_basic", "dollar")
    r = 22; data_row(r, "Full Year EPS (Diluted)", "net_income_and_eps", "full_year_eps_diluted", "dollar")

    # Cash Flow Summary
    r = 24
    ws.merge_range(r, 0, r, len(labels), "CASH FLOW SUMMARY", fmts["section"])
    r = 25; data_row(r, "Operating Cash Flow", "cash_flow", "operating_cash_flow")
    r = 26; data_row(r, "Free Cash Flow", "cash_flow", "free_cash_flow")
    r = 27; data_row(r, "CapEx (PP&E Purchases)", "capex", "total_capex")

    # --- Charts ---

    # Revenue comparison chart
    chart = wb.add_chart({"type": "column"})
    for i, l in enumerate(labels):
        chart.add_series({
            "name": l,
            "categories": ["Financials", 3, 0, 4, 0],
            "values": ["Financials", 3, 1 + i, 4, 1 + i],
            "fill": {"color": AMZN_COLOR if l == "Amazon" else AAPL_COLOR},
            "data_labels": {"value": True, "num_format": "$#,##0", "font": {"size": 9}},
        })
    chart.set_title({"name": "Quarterly Net Sales ($M)"})
    chart.set_y_axis({"num_format": "#,##0"})
    chart.set_size({"width": 520, "height": 320})
    ws.insert_chart("E2", chart)

    # Margin comparison chart
    chart2 = wb.add_chart({"type": "column"})
    for i, l in enumerate(labels):
        chart2.add_series({
            "name": l,
            "categories": ["Financials", 12, 0, 12, 0],
            "values": ["Financials", 12, 1 + i, 12, 1 + i],
            "fill": {"color": AMZN_COLOR if l == "Amazon" else AAPL_COLOR},
            "data_labels": {"value": True, "num_format": "0.0%", "font": {"size": 9}},
        })
    chart2.set_title({"name": "Quarterly Operating Margin"})
    chart2.set_y_axis({"num_format": "0%"})
    chart2.set_size({"width": 520, "height": 320})
    ws.insert_chart("E18", chart2)

    return ws


def build_segments(wb, companies, fmts):
    ws = wb.add_worksheet("Segments")
    ws.set_column(0, 0, 24)
    ws.set_column(1, 6, 20)

    r = 0
    for label, info in companies.items():
        segments = info["data"].get("segments", [])
        if not segments:
            continue

        ws.merge_range(r, 0, r, 6, f"{label} Segments ({info['period']})", fmts["section"])
        r += 1
        headers = ["Segment", "Net Sales ($M)", "Prior Year ($M)", "YoY Growth", "Op Income ($M)", "Op Margin", "Revenue Mix"]
        for c, h in enumerate(headers):
            ws.write(r, c, h, fmts["header"])
        r += 1

        data_start = r
        for seg in segments:
            alt = ((r - data_start) % 2 == 1)
            fl = fmts["alt_label"] if alt else fmts["label"]
            fn = fmts["alt_num"] if alt else fmts["num"]
            fp = fmts["alt_pct"] if alt else fmts["pct"]

            ws.write(r, 0, seg.get("segment_name", ""), fl)
            ws.write(r, 1, seg.get("quarterly_net_sales", 0), fn)
            ws.write(r, 2, seg.get("quarterly_prior_year_net_sales", 0), fn)
            g = seg.get("quarterly_yoy_growth_pct")
            if g is not None:
                ws.write(r, 3, g / 100, fp)
            ws.write(r, 4, seg.get("quarterly_operating_income", 0), fn)
            m = seg.get("quarterly_operating_margin_pct")
            if m is not None:
                ws.write(r, 5, m / 100, fp)
            mx = seg.get("revenue_mix_pct")
            if mx is not None:
                ws.write(r, 6, mx / 100, fp)
            r += 1

        # Pie chart for revenue mix
        pie = wb.add_chart({"type": "pie"})
        pie.add_series({
            "name": f"{label} Revenue Mix",
            "categories": ["Segments", data_start, 0, data_start + len(segments) - 1, 0],
            "values": ["Segments", data_start, 1, data_start + len(segments) - 1, 1],
            "data_labels": {"percentage": True, "category": True, "num_format": "$#,##0", "font": {"size": 9}, "separator": "\n"},
        })
        pie.set_title({"name": f"{label} Revenue Mix ($M)"})
        pie.set_size({"width": 500, "height": 350})
        pie.set_legend({"position": "right"})

        # Bar chart for segment operating margin
        bar = wb.add_chart({"type": "bar"})
        bar.add_series({
            "name": "Operating Margin",
            "categories": ["Segments", data_start, 0, data_start + len(segments) - 1, 0],
            "values": ["Segments", data_start, 5, data_start + len(segments) - 1, 5],
            "fill": {"color": AMZN_COLOR if label == "Amazon" else AAPL_COLOR},
            "data_labels": {"value": True, "num_format": "0.0%", "font": {"size": 9}},
        })
        bar.set_title({"name": f"{label} Segment Op Margin"})
        bar.set_x_axis({"num_format": "0%"})
        bar.set_size({"width": 450, "height": 320})
        bar.set_legend({"none": True})

        ws.insert_chart(f"I{data_start - 1}", pie)
        ws.insert_chart(f"I{data_start + 15}", bar)

        r += 2

    return ws


def build_cash_flow(wb, companies, fmts):
    ws = wb.add_worksheet("Cash Flow")
    labels = list(companies.keys())
    ws.set_column(0, 0, 36)
    ws.set_column(1, len(labels), 30)

    r = 0
    ws.write(r, 0, "Metric ($M)", fmts["header"])
    for i, l in enumerate(labels):
        ws.write(r, 1 + i, f"{l} ({companies[l]['period']})", fmts["header"])

    def nested_get(data, *keys):
        v = data
        for k in keys:
            if isinstance(v, dict):
                v = v.get(k)
            else:
                return None
        return v

    def data_row(row, name, *keys):
        alt = (row % 2 == 0)
        fl = fmts["alt_label"] if alt else fmts["label"]
        fn = fmts["alt_num"] if alt else fmts["num"]
        ws.write(row, 0, name, fl)
        for i, l in enumerate(labels):
            v = nested_get(companies[l]["data"], *keys)
            if v and v != 0:
                ws.write(row, 1 + i, v, fn)

    # CapEx
    r = 2; ws.merge_range(r, 0, r, len(labels), "CAPITAL EXPENDITURES", fmts["section"])
    r = 3; data_row(r, "Purchases of PP&E", "cash_flow_and_liquidity", "capital_expenditures", "purchases_of_property_and_equipment")
    r = 4; data_row(r, "Finance Lease Additions", "cash_flow_and_liquidity", "capital_expenditures", "finance_lease_additions")
    r = 5; data_row(r, "Proceeds from Asset Sales", "cash_flow_and_liquidity", "capital_expenditures", "proceeds_from_asset_sales")

    # Debt
    r = 7; ws.merge_range(r, 0, r, len(labels), "DEBT SERVICE", fmts["section"])
    r = 8; data_row(r, "Long-Term Debt Repayments", "cash_flow_and_liquidity", "debt_repayments", "long_term_debt_repayments")
    r = 9; data_row(r, "Short-Term Debt Repayments", "cash_flow_and_liquidity", "debt_repayments", "short_term_debt_repayments")

    # Leases
    r = 11; ws.merge_range(r, 0, r, len(labels), "LEASE OBLIGATIONS", fmts["section"])
    r = 12; data_row(r, "Finance Lease Repayments", "cash_flow_and_liquidity", "lease_obligations", "finance_lease_principal_repayments")
    r = 13; data_row(r, "Operating Lease Payments", "cash_flow_and_liquidity", "lease_obligations", "operating_lease_payments")

    # Liquidity
    r = 15; ws.merge_range(r, 0, r, len(labels), "LIQUIDITY", fmts["section"])
    cash_row = 16; data_row(cash_row, "Cash & Equivalents", "cash_flow_and_liquidity", "liquidity", "cash_and_equivalents")
    sec_row = 17; data_row(sec_row, "Current Marketable Securities", "cash_flow_and_liquidity", "liquidity", "current_marketable_securities")
    nsec_row = 18; data_row(nsec_row, "Non-Current Marketable Securities", "cash_flow_and_liquidity", "liquidity", "non_current_marketable_securities")
    debt_row = 19; data_row(debt_row, "Total Debt", "cash_flow_and_liquidity", "liquidity", "total_debt")

    # OCF vs CapEx vs FCF chart
    chart = wb.add_chart({"type": "column"})
    # We need a mini data block for the chart
    r = 22
    ws.write(r, 0, "", fmts["label"])
    ws.write(r, 1, "Operating CF", fmts["header"])
    ws.write(r, 2, "CapEx", fmts["header"])
    ws.write(r, 3, "Free CF", fmts["header"])
    for i, l in enumerate(labels):
        ws.write(r + 1 + i, 0, l, fmts["label"])
        ws.write(r + 1 + i, 1, companies[l]["data"]["cash_flow"]["operating_cash_flow"], fmts["num"])
        ws.write(r + 1 + i, 2, companies[l]["data"]["capex"]["total_capex"], fmts["num"])
        ws.write(r + 1 + i, 3, companies[l]["data"]["cash_flow"]["free_cash_flow"], fmts["num"])

    chart.add_series({
        "name": "Operating CF",
        "categories": ["Cash Flow", r + 1, 0, r + len(labels), 0],
        "values": ["Cash Flow", r + 1, 1, r + len(labels), 1],
        "fill": {"color": "#2196F3"},
        "data_labels": {"value": True, "num_format": "$#,##0", "font": {"size": 9}},
    })
    chart.add_series({
        "name": "CapEx",
        "categories": ["Cash Flow", r + 1, 0, r + len(labels), 0],
        "values": ["Cash Flow", r + 1, 2, r + len(labels), 2],
        "fill": {"color": "#F44336"},
        "data_labels": {"value": True, "num_format": "$#,##0", "font": {"size": 9}},
    })
    chart.add_series({
        "name": "Free CF",
        "categories": ["Cash Flow", r + 1, 0, r + len(labels), 0],
        "values": ["Cash Flow", r + 1, 3, r + len(labels), 3],
        "fill": {"color": "#4CAF50"},
        "data_labels": {"value": True, "num_format": "$#,##0", "font": {"size": 9}},
    })
    chart.set_title({"name": "Operating CF vs CapEx vs Free CF ($M)"})
    chart.set_y_axis({"num_format": "#,##0"})
    chart.set_size({"width": 520, "height": 340})
    ws.insert_chart("E2", chart)

    # Liquidity chart
    lchart = wb.add_chart({"type": "column"})
    r2 = r + len(labels) + 2
    ws.write(r2, 0, "", fmts["label"])
    ws.write(r2, 1, "Cash & Securities", fmts["header"])
    ws.write(r2, 2, "Total Debt", fmts["header"])
    for i, l in enumerate(labels):
        liq = companies[l]["data"].get("cash_flow_and_liquidity", {}).get("liquidity", {})
        total_cash = (liq.get("cash_and_equivalents", 0) or 0) + \
                     (liq.get("current_marketable_securities", 0) or 0) + \
                     (liq.get("non_current_marketable_securities", 0) or 0)
        debt = liq.get("total_debt", 0) or 0
        ws.write(r2 + 1 + i, 0, l, fmts["label"])
        ws.write(r2 + 1 + i, 1, total_cash, fmts["num"])
        ws.write(r2 + 1 + i, 2, debt, fmts["num"])

    lchart.add_series({
        "name": "Cash & Securities",
        "categories": ["Cash Flow", r2 + 1, 0, r2 + len(labels), 0],
        "values": ["Cash Flow", r2 + 1, 1, r2 + len(labels), 1],
        "fill": {"color": "#4CAF50"},
        "data_labels": {"value": True, "num_format": "$#,##0", "font": {"size": 9}},
    })
    lchart.add_series({
        "name": "Total Debt",
        "categories": ["Cash Flow", r2 + 1, 0, r2 + len(labels), 0],
        "values": ["Cash Flow", r2 + 1, 2, r2 + len(labels), 2],
        "fill": {"color": "#F44336"},
        "data_labels": {"value": True, "num_format": "$#,##0", "font": {"size": 9}},
    })
    lchart.set_title({"name": "Cash & Securities vs Total Debt ($M)"})
    lchart.set_y_axis({"num_format": "#,##0"})
    lchart.set_size({"width": 520, "height": 340})
    ws.insert_chart("E20", lchart)

    return ws


def build_guidance(wb, companies, fmts):
    ws = wb.add_worksheet("Guidance")
    labels = list(companies.keys())
    ws.set_column(0, 0, 28)
    ws.set_column(1, len(labels), 30)

    r = 0
    ws.write(r, 0, "Metric", fmts["header"])
    for i, l in enumerate(labels):
        ws.write(r, 1 + i, l, fmts["header"])

    r = 2; ws.merge_range(r, 0, r, len(labels), "FORWARD GUIDANCE", fmts["section"])

    def guidance_row(row, name, key, fmt_type="num"):
        alt = (row % 2 == 0)
        fl = fmts["alt_label"] if alt else fmts["label"]
        fv = fmts[f"alt_{fmt_type}"] if alt else fmts[fmt_type]
        ft = fmts["text_center"]
        ws.write(row, 0, name, fl)
        for i, l in enumerate(labels):
            fg = companies[l]["data"].get("forward_guidance", {})
            if not fg.get("has_guidance"):
                ws.write(row, 1 + i, "Not provided", ft)
            else:
                v = fg.get(key)
                if v is not None:
                    if fmt_type == "pct":
                        v = v / 100
                    ws.write(row, 1 + i, v, fv)

    r = 3; guidance_row(r, "Guidance Period", "guidance_period", "text")
    r = 4; guidance_row(r, "Revenue Low ($M)", "revenue_low")
    r = 5; guidance_row(r, "Revenue High ($M)", "revenue_high")
    r = 6; guidance_row(r, "Revenue Growth Low", "revenue_growth_low_pct", "pct")
    r = 7; guidance_row(r, "Revenue Growth High", "revenue_growth_high_pct", "pct")
    r = 8; guidance_row(r, "Operating Income Low ($M)", "operating_income_low")
    r = 9; guidance_row(r, "Operating Income High ($M)", "operating_income_high")
    r = 11; ws.merge_range(r, 0, r, len(labels), "FX IMPACT", fmts["section"])
    r = 12; guidance_row(r, "FX Impact ($M)", "fx_impact_amount")
    r = 13; guidance_row(r, "FX Impact (bps)", "fx_impact_bps")

    # Guidance range chart (Amazon only if available)
    amzn_fg = companies.get("Amazon", {}).get("data", {}).get("forward_guidance", {})
    if amzn_fg.get("has_guidance"):
        chart = wb.add_chart({"type": "bar"})
        # Write chart data
        r = 16
        ws.write(r, 0, "", fmts["label"])
        ws.write(r, 1, "Low", fmts["header"])
        ws.write(r, 2, "Range", fmts["header"])
        ws.write(r + 1, 0, "Revenue", fmts["label"])
        ws.write(r + 1, 1, amzn_fg["revenue_low"], fmts["num"])
        ws.write(r + 1, 2, amzn_fg["revenue_high"] - amzn_fg["revenue_low"], fmts["num"])
        ws.write(r + 2, 0, "Operating Income", fmts["label"])
        ws.write(r + 2, 1, amzn_fg["operating_income_low"], fmts["num"])
        ws.write(r + 2, 2, amzn_fg["operating_income_high"] - amzn_fg["operating_income_low"], fmts["num"])

        # Stacked bar: invisible base + visible range
        chart.add_series({
            "name": "Low",
            "categories": ["Guidance", r + 1, 0, r + 2, 0],
            "values": ["Guidance", r + 1, 1, r + 2, 1],
            "fill": {"none": True},
            "border": {"none": True},
        })
        chart.add_series({
            "name": "Range",
            "categories": ["Guidance", r + 1, 0, r + 2, 0],
            "values": ["Guidance", r + 1, 2, r + 2, 2],
            "fill": {"color": AMZN_COLOR},
            "data_labels": {"value": True, "num_format": "$#,##0", "font": {"size": 9}, "position": "outside_end"},
        })
        chart.set_title({"name": f"Amazon Guidance Range — {amzn_fg.get('guidance_period', '')}"})
        chart.set_x_axis({"num_format": "$#,##0"})
        chart.set_style(10)
        chart.set_size({"width": 520, "height": 280})
        chart.set_legend({"position": "bottom"})
        ws.insert_chart("E2", chart)

    return ws


def build_notes(wb, companies, fmts):
    ws = wb.add_worksheet("Notes")
    labels = list(companies.keys())
    ws.set_column(0, 0, 32)
    ws.set_column(1, len(labels), 30)

    r = 0
    ws.write(r, 0, "Metric", fmts["header"])
    for i, l in enumerate(labels):
        ws.write(r, 1 + i, f"{l} ({companies[l]['period']})", fmts["header"])

    # SBC
    r = 2; ws.merge_range(r, 0, r, len(labels), "STOCK-BASED COMPENSATION ($M)", fmts["section"])

    def sbc_row(row, name, key):
        alt = (row % 2 == 0)
        fl = fmts["alt_label"] if alt else fmts["label"]
        fn = fmts["alt_num"] if alt else fmts["num"]
        ws.write(row, 0, name, fl)
        for i, l in enumerate(labels):
            v = companies[l]["data"].get("key_business_metrics", {}).get("stock_based_compensation", {}).get(key)
            if v:
                ws.write(row, 1 + i, v, fn)

    r = 3; sbc_row(r, "Quarterly SBC", "quarterly_sbc")
    r = 4; sbc_row(r, "Prior Year Quarter SBC", "quarterly_prior_year_sbc")
    r = 5; sbc_row(r, "Full Year SBC", "full_year_sbc")
    r = 6; sbc_row(r, "Prior Full Year SBC", "full_year_prior_year_sbc")

    # KPIs
    r = 8; ws.merge_range(r, 0, r, 2, "OPERATIONAL KPIs", fmts["section"])
    r += 1
    for label, info in companies.items():
        kpis = info["data"].get("key_business_metrics", {}).get("operational_kpis", [])
        if kpis:
            ws.write(r, 0, f"{label} KPIs", fmts["section"])
            ws.write(r, 1, "Current Value", fmts["header"])
            ws.write(r, 2, "YoY Change", fmts["header"])
            r += 1
            for kpi in kpis:
                ws.write(r, 0, kpi.get("metric_name", ""), fmts["label"])
                ws.write(r, 1, kpi.get("current_value", ""), fmts["text_center"])
                ws.write(r, 2, kpi.get("yoy_change", ""), fmts["text_center"])
                r += 1
            r += 1

    # Assumptions
    r += 1
    ws.merge_range(r, 0, r, len(labels), "ASSUMPTIONS & ADJUSTMENTS", fmts["section"])
    notes = [
        "All monetary values in $M unless noted",
        "Free cash flow = Operating Cash Flow - CapEx (computed) for companies that do not report it directly",
        "Growth percentages calculated: (current - prior) / prior * 100",
        "Apple does not provide forward guidance",
    ]
    for note in notes:
        r += 1
        ws.write(r, 0, note, fmts["text"])

    return ws


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "v8"
    out_dir = ROOT / "sheets" / version
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "Portfolio Extraction with Reducto AI.xlsx"

    companies = load_data(version)
    print(f"Generating {out_path.relative_to(ROOT)}")

    wb = xlsxwriter.Workbook(str(out_path))
    fmts = make_formats(wb)

    build_financials(wb, companies, fmts)
    build_segments(wb, companies, fmts)
    build_cash_flow(wb, companies, fmts)
    build_guidance(wb, companies, fmts)
    build_notes(wb, companies, fmts)

    wb.close()
    print(f"Done. Upload {out_path.name} to Google Drive or open in Excel.")


if __name__ == "__main__":
    main()
