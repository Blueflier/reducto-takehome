"""
Web app: Upload PDFs → Reducto extract → Download formatted Excel.

Usage:
    cd web && uvicorn app:app --reload --port 8000
"""

import asyncio
import io
import json
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from reducto import Reducto

import xlsxwriter

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

_V9 = json.loads((ROOT / "schemas" / "v9" / "schema.json").read_text())
SYSTEM_PROMPT = _V9["instructions"]["system_prompt"]


def _to_json_schema(fields: list[dict]) -> dict:
    """Convert Reducto native schema (name/subfields) to JSON Schema (type/properties)."""
    def convert(field):
        t = field.get("type", "object")
        result = {"description": field.get("description", "")}
        if t == "array":
            result["type"] = "array"
            if "subfields" in field:
                result["items"] = {"type": "object", "properties": {
                    sf["name"]: convert(sf) for sf in field["subfields"]
                }}
        elif t == "object" or "subfields" in field:
            result["type"] = "object"
            if "subfields" in field:
                result["properties"] = {sf["name"]: convert(sf) for sf in field["subfields"]}
        elif t == "text":
            result["type"] = "string"
        else:
            result["type"] = t
        return result
    return {"type": "object", "properties": {f["name"]: convert(f) for f in fields}}


SCHEMA = _to_json_schema(_V9["instructions"]["schema"])

# Colors
COMPANY_COLORS = ["#FF9900", "#555555", "#2196F3", "#4CAF50", "#9C27B0"]
SEGMENT_PALETTE = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336", "#00BCD4"]
HEADER_BG = "#1F4E79"
SECTION_BG = "#D6E4F0"
ALT_ROW_BG = "#F2F7FB"

app = FastAPI(title="Portfolio Extraction with Reducto AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def compute_derived_fields(data: dict) -> dict:
    cf = data.get("cash_flow", {})
    capex = data.get("capex", {})
    op_cf = cf.get("operating_cash_flow")
    pp_e = capex.get("total_capex")
    if op_cf and pp_e and not cf.get("free_cash_flow"):
        cf["free_cash_flow"] = op_cf - pp_e
    return data


def extract_pdf(client: Reducto, file_bytes: bytes, filename: str) -> dict:
    """Parse and extract a single PDF, return extraction data."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(file_bytes)
        tmp_path = Path(f.name)

    upload = client.upload(file=tmp_path)
    parse_result = client.parse.run(input=upload)
    job_id = parse_result.job_id

    result = client.extract.run(
        input=f"jobid://{job_id}",
        instructions={"schema": SCHEMA, "system_prompt": SYSTEM_PROMPT},
    )

    data = result.result[0] if result.result else {}
    data = compute_derived_fields(data)

    tmp_path.unlink(missing_ok=True)
    return data


def make_formats(wb):
    f = {}
    f["header"] = wb.add_format({"bold": True, "font_color": "white", "bg_color": HEADER_BG, "border": 1, "font_size": 11, "align": "center"})
    f["section"] = wb.add_format({"bold": True, "bg_color": SECTION_BG, "border": 1, "font_size": 11})
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


def build_financials(wb, companies, fmts):
    ws = wb.add_worksheet("Financials")
    labels = list(companies.keys())
    ws.set_column(0, 0, 32)
    ws.set_column(1, len(labels), 30)

    r = 0
    ws.write(r, 0, "Metric (in $M except per-share)", fmts["header"])
    for i, l in enumerate(labels):
        ws.write(r, 1 + i, l, fmts["header"])

    def get(label, section, key):
        return companies[label].get(section, {}).get(key)

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

    r = 2; ws.merge_range(r, 0, r, len(labels), "NET SALES", fmts["section"])
    r = 3; data_row(r, "Quarterly Net Sales", "total_net_sales", "quarterly_sales")
    r = 4; data_row(r, "Prior Year Quarter", "total_net_sales", "quarterly_prior_year_sales")
    r = 5; data_row(r, "Quarterly YoY Growth", "total_net_sales", "quarterly_growth_pct", "pct")
    r = 6; data_row(r, "Full Year Net Sales", "total_net_sales", "full_year_sales")
    r = 7; data_row(r, "Prior Full Year", "total_net_sales", "full_year_prior_year_sales")
    r = 8; data_row(r, "Full Year YoY Growth", "total_net_sales", "full_year_growth_pct", "pct")

    r = 10; ws.merge_range(r, 0, r, len(labels), "OPERATING INCOME", fmts["section"])
    r = 11; data_row(r, "Quarterly Operating Income", "operating_income", "quarterly_operating_income")
    r = 12; data_row(r, "Quarterly Operating Margin", "operating_income", "quarterly_operating_margin_pct", "pct")
    r = 13; data_row(r, "Full Year Operating Income", "operating_income", "full_year_operating_income")
    r = 14; data_row(r, "Full Year Operating Margin", "operating_income", "full_year_operating_margin_pct", "pct")

    r = 16; ws.merge_range(r, 0, r, len(labels), "NET INCOME & EPS", fmts["section"])
    r = 17; data_row(r, "Quarterly Net Income", "net_income_and_eps", "quarterly_net_income")
    r = 18; data_row(r, "Quarterly EPS (Basic)", "net_income_and_eps", "quarterly_eps_basic", "dollar")
    r = 19; data_row(r, "Quarterly EPS (Diluted)", "net_income_and_eps", "quarterly_eps_diluted", "dollar")
    r = 20; data_row(r, "Full Year Net Income", "net_income_and_eps", "full_year_net_income")
    r = 21; data_row(r, "Full Year EPS (Basic)", "net_income_and_eps", "full_year_eps_basic", "dollar")
    r = 22; data_row(r, "Full Year EPS (Diluted)", "net_income_and_eps", "full_year_eps_diluted", "dollar")

    r = 24; ws.merge_range(r, 0, r, len(labels), "CASH FLOW SUMMARY", fmts["section"])
    r = 25; data_row(r, "Operating Cash Flow", "cash_flow", "operating_cash_flow")
    r = 26; data_row(r, "Free Cash Flow", "cash_flow", "free_cash_flow")
    r = 27; data_row(r, "CapEx (PP&E Purchases)", "capex", "total_capex")

    # Revenue chart
    chart = wb.add_chart({"type": "column"})
    for i, l in enumerate(labels):
        chart.add_series({
            "name": l,
            "categories": ["Financials", 3, 0, 4, 0],
            "values": ["Financials", 3, 1 + i, 4, 1 + i],
            "fill": {"color": COMPANY_COLORS[i % len(COMPANY_COLORS)]},
            "data_labels": {"value": True, "num_format": "$#,##0", "font": {"size": 9}},
        })
    chart.set_title({"name": "Quarterly Net Sales ($M)"})
    chart.set_y_axis({"num_format": "#,##0"})
    chart.set_size({"width": 520, "height": 320})
    ws.insert_chart("E2", chart)

    # Margin chart
    chart2 = wb.add_chart({"type": "column"})
    for i, l in enumerate(labels):
        chart2.add_series({
            "name": l,
            "categories": ["Financials", 12, 0, 12, 0],
            "values": ["Financials", 12, 1 + i, 12, 1 + i],
            "fill": {"color": COMPANY_COLORS[i % len(COMPANY_COLORS)]},
            "data_labels": {"value": True, "num_format": "0.0%", "font": {"size": 9}},
        })
    chart2.set_title({"name": "Quarterly Operating Margin"})
    chart2.set_y_axis({"num_format": "0%"})
    chart2.set_size({"width": 520, "height": 320})
    ws.insert_chart("E18", chart2)


def build_segments(wb, companies, fmts):
    ws = wb.add_worksheet("Segments")
    ws.set_column(0, 0, 24)
    ws.set_column(1, 6, 20)
    labels = list(companies.keys())

    PIE_ROWS = 22   # ~350px at default row height (15px)
    BAR_ROWS = 20   # ~320px at default row height
    CHART_GAP = 1   # blank rows between charts

    r = 0
    chart_row = 0   # tracks next available row in chart column (I)
    for idx, (label, data) in enumerate(companies.items()):
        segments = data.get("segments", [])
        if not segments:
            continue

        ws.merge_range(r, 0, r, 6, f"{label} Segments", fmts["section"])
        r += 1
        for c, h in enumerate(["Segment", "Net Sales ($M)", "Prior Year ($M)", "YoY Growth", "Op Income ($M)", "Op Margin", "Revenue Mix"]):
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

        pie = wb.add_chart({"type": "pie"})
        pie.add_series({
            "name": f"{label} Revenue Mix",
            "categories": ["Segments", data_start, 0, data_start + len(segments) - 1, 0],
            "values": ["Segments", data_start, 1, data_start + len(segments) - 1, 1],
            "data_labels": {"percentage": True, "category": True, "font": {"size": 9}, "separator": "\n"},
        })
        pie.set_title({"name": f"{label} Revenue Mix ($M)"})
        pie.set_size({"width": 500, "height": 350})
        pie.set_legend({"position": "right"})
        ws.insert_chart(f"I{chart_row + 1}", pie)
        chart_row += PIE_ROWS + CHART_GAP

        bar = wb.add_chart({"type": "bar"})
        bar.add_series({
            "name": "Operating Margin",
            "categories": ["Segments", data_start, 0, data_start + len(segments) - 1, 0],
            "values": ["Segments", data_start, 5, data_start + len(segments) - 1, 5],
            "fill": {"color": COMPANY_COLORS[idx % len(COMPANY_COLORS)]},
            "data_labels": {"value": True, "num_format": "0.0%", "font": {"size": 9}},
        })
        bar.set_title({"name": f"{label} Segment Op Margin"})
        bar.set_x_axis({"num_format": "0%"})
        bar.set_size({"width": 450, "height": 320})
        bar.set_legend({"none": True})
        ws.insert_chart(f"I{chart_row + 1}", bar)
        chart_row += BAR_ROWS + CHART_GAP

        r += 2


def build_cash_flow(wb, companies, fmts):
    ws = wb.add_worksheet("Cash Flow")
    labels = list(companies.keys())
    ws.set_column(0, 0, 36)
    ws.set_column(1, len(labels), 30)

    r = 0
    ws.write(r, 0, "Metric ($M)", fmts["header"])
    for i, l in enumerate(labels):
        ws.write(r, 1 + i, l, fmts["header"])

    def nested_get(data, *keys):
        v = data
        for k in keys:
            v = v.get(k) if isinstance(v, dict) else None
        return v

    def data_row(row, name, *keys):
        alt = (row % 2 == 0)
        fl = fmts["alt_label"] if alt else fmts["label"]
        fn = fmts["alt_num"] if alt else fmts["num"]
        ws.write(row, 0, name, fl)
        for i, l in enumerate(labels):
            v = nested_get(companies[l], *keys)
            if v and v != 0:
                ws.write(row, 1 + i, v, fn)

    r = 2; ws.merge_range(r, 0, r, len(labels), "CAPITAL EXPENDITURES", fmts["section"])
    r = 3; data_row(r, "Purchases of PP&E", "cash_flow_and_liquidity", "capital_expenditures", "purchases_of_property_and_equipment")
    r = 4; data_row(r, "Finance Lease Additions", "cash_flow_and_liquidity", "capital_expenditures", "finance_lease_additions")
    r = 5; data_row(r, "Proceeds from Asset Sales", "cash_flow_and_liquidity", "capital_expenditures", "proceeds_from_asset_sales")
    r = 7; ws.merge_range(r, 0, r, len(labels), "DEBT SERVICE", fmts["section"])
    r = 8; data_row(r, "Long-Term Debt Repayments", "cash_flow_and_liquidity", "debt_repayments", "long_term_debt_repayments")
    r = 9; data_row(r, "Short-Term Debt Repayments", "cash_flow_and_liquidity", "debt_repayments", "short_term_debt_repayments")
    r = 11; ws.merge_range(r, 0, r, len(labels), "LEASE OBLIGATIONS", fmts["section"])
    r = 12; data_row(r, "Finance Lease Repayments", "cash_flow_and_liquidity", "lease_obligations", "finance_lease_principal_repayments")
    r = 13; data_row(r, "Operating Lease Payments", "cash_flow_and_liquidity", "lease_obligations", "operating_lease_payments")
    r = 15; ws.merge_range(r, 0, r, len(labels), "LIQUIDITY", fmts["section"])
    r = 16; data_row(r, "Cash & Equivalents", "cash_flow_and_liquidity", "liquidity", "cash_and_equivalents")
    r = 17; data_row(r, "Current Marketable Securities", "cash_flow_and_liquidity", "liquidity", "current_marketable_securities")
    r = 18; data_row(r, "Non-Current Marketable Securities", "cash_flow_and_liquidity", "liquidity", "non_current_marketable_securities")
    r = 19; data_row(r, "Total Debt", "cash_flow_and_liquidity", "liquidity", "total_debt")

    # Chart data block
    r = 22
    ws.write(r, 0, "", fmts["label"])
    ws.write(r, 1, "Operating CF", fmts["header"])
    ws.write(r, 2, "CapEx", fmts["header"])
    ws.write(r, 3, "Free CF", fmts["header"])
    for i, l in enumerate(labels):
        ws.write(r + 1 + i, 0, l, fmts["label"])
        ws.write(r + 1 + i, 1, companies[l].get("cash_flow", {}).get("operating_cash_flow", 0), fmts["num"])
        ws.write(r + 1 + i, 2, companies[l].get("capex", {}).get("total_capex", 0), fmts["num"])
        ws.write(r + 1 + i, 3, companies[l].get("cash_flow", {}).get("free_cash_flow", 0), fmts["num"])

    chart = wb.add_chart({"type": "column"})
    for col, (name, color) in enumerate(zip(["Operating CF", "CapEx", "Free CF"], ["#2196F3", "#F44336", "#4CAF50"])):
        chart.add_series({
            "name": name,
            "categories": ["Cash Flow", r + 1, 0, r + len(labels), 0],
            "values": ["Cash Flow", r + 1, 1 + col, r + len(labels), 1 + col],
            "fill": {"color": color},
            "data_labels": {"value": True, "num_format": "$#,##0", "font": {"size": 9}},
        })
    chart.set_title({"name": "Operating CF vs CapEx vs Free CF ($M)"})
    chart.set_y_axis({"num_format": "#,##0"})
    chart.set_size({"width": 520, "height": 340})
    ws.insert_chart("E2", chart)


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
            fg = companies[l].get("forward_guidance", {})
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


def build_notes(wb, companies, fmts):
    ws = wb.add_worksheet("Notes")
    labels = list(companies.keys())
    ws.set_column(0, 0, 32)
    ws.set_column(1, len(labels), 30)

    r = 0
    ws.write(r, 0, "Metric", fmts["header"])
    for i, l in enumerate(labels):
        ws.write(r, 1 + i, l, fmts["header"])

    r = 2; ws.merge_range(r, 0, r, len(labels), "STOCK-BASED COMPENSATION ($M)", fmts["section"])

    def sbc_row(row, name, key):
        alt = (row % 2 == 0)
        fl = fmts["alt_label"] if alt else fmts["label"]
        fn = fmts["alt_num"] if alt else fmts["num"]
        ws.write(row, 0, name, fl)
        for i, l in enumerate(labels):
            v = companies[l].get("key_business_metrics", {}).get("stock_based_compensation", {}).get(key)
            if v:
                ws.write(row, 1 + i, v, fn)

    r = 3; sbc_row(r, "Quarterly SBC", "quarterly_sbc")
    r = 4; sbc_row(r, "Prior Year Quarter SBC", "quarterly_prior_year_sbc")
    r = 5; sbc_row(r, "Full Year SBC", "full_year_sbc")
    r = 6; sbc_row(r, "Prior Full Year SBC", "full_year_prior_year_sbc")

    r = 8; ws.merge_range(r, 0, r, 2, "OPERATIONAL KPIs", fmts["section"])
    r += 1
    for label, data in companies.items():
        kpis = data.get("key_business_metrics", {}).get("operational_kpis", [])
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

    r += 1
    ws.merge_range(r, 0, r, len(labels), "ASSUMPTIONS & ADJUSTMENTS", fmts["section"])
    for note in [
        "All monetary values in $M unless noted",
        "Free cash flow = Operating Cash Flow - CapEx (computed) when not directly reported",
        "Growth percentages calculated: (current - prior) / prior * 100",
    ]:
        r += 1
        ws.write(r, 0, note, fmts["text"])


def generate_xlsx(companies: dict[str, dict]) -> Path:
    """Generate xlsx from extraction data, return path to file."""
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    tmp.close()

    wb = xlsxwriter.Workbook(tmp.name)
    fmts = make_formats(wb)

    build_financials(wb, companies, fmts)
    build_segments(wb, companies, fmts)
    build_cash_flow(wb, companies, fmts)
    build_guidance(wb, companies, fmts)
    build_notes(wb, companies, fmts)

    wb.close()
    return Path(tmp.name)


# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def index():
    return (Path(__file__).parent / "index.html").read_text()


@app.get("/logo.jpg")
async def logo():
    return FileResponse(path=str(ROOT / "Reducto_logo_large_Logo.jpg"), media_type="image/jpeg")


@app.post("/extract-one")
async def extract_one(file: UploadFile = File(...)):
    """Extract a single PDF and return JSON. Multiple calls run in parallel from the frontend."""
    client = Reducto()
    content = await file.read()
    label = file.filename.replace(".pdf", "").replace(".PDF", "")
    data = await asyncio.to_thread(extract_pdf, client, content, file.filename)
    return {label: data}


@app.post("/build-xlsx")
async def build_xlsx(payload: dict):
    """Combine pre-extracted company data into a single Excel file."""
    companies = payload.get("companies", {})
    xlsx_path = generate_xlsx(companies)
    return FileResponse(
        path=str(xlsx_path),
        filename="Portfolio Extraction with Reducto AI.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
