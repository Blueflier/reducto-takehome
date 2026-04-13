"""
Generate chart PNGs from extraction JSON for Google Sheets.

Usage:
    python generate_charts.py v8

Outputs to charts/<version>/ with one PNG per chart.
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

ROOT = Path(__file__).parent

# Consistent styling
COLORS = {
    "Amazon": "#FF9900",
    "Apple": "#555555",
}
SEGMENT_PALETTE = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336", "#00BCD4"]

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.alpha": 0.3,
    "font.size": 11,
    "figure.dpi": 150,
})


def load_data(version: str) -> dict:
    schema_dir = ROOT / "schemas" / version
    companies = {}
    for path in sorted(schema_dir.glob("*.extract.json")):
        name = path.name.replace(f".{version}.extract.json", "")
        if "AMZN" in name:
            label = "Amazon"
        elif "10-Q" in name:
            label = "Apple"
        else:
            label = name
        with open(path) as f:
            companies[label] = json.load(f)
    return companies


def save(fig, out_dir: Path, name: str):
    path = out_dir / f"{name}.png"
    fig.savefig(path, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    print(f"  {name}.png")


# --- Chart 1: Revenue Comparison ---
def chart_revenue(companies: dict, out_dir: Path):
    fig, ax = plt.subplots(figsize=(10, 5))

    labels_list = list(companies.keys())
    metrics = ["Quarterly", "Prior Year Q", "Full Year", "Prior Full Year"]
    keys = [
        ("total_net_sales", "quarterly_sales"),
        ("total_net_sales", "quarterly_prior_year_sales"),
        ("total_net_sales", "full_year_sales"),
        ("total_net_sales", "full_year_prior_year_sales"),
    ]

    x = np.arange(len(metrics))
    width = 0.35

    for i, label in enumerate(labels_list):
        vals = [companies[label].get(s, {}).get(k, 0) for s, k in keys]
        bars = ax.bar(x + i * width, vals, width, label=label, color=COLORS.get(label, "#999"))
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"${val:,.0f}", ha="center", va="bottom", fontsize=8)

    ax.set_ylabel("$M")
    ax.set_title("Net Sales Comparison")
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(metrics)
    ax.legend()
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    save(fig, out_dir, "1_revenue_comparison")


# --- Chart 2: Operating Margin Comparison ---
def chart_margins(companies: dict, out_dir: Path):
    fig, ax = plt.subplots(figsize=(8, 5))

    labels_list = list(companies.keys())
    metrics = ["Quarterly Op Margin", "Full Year Op Margin"]
    keys = [
        ("operating_income", "quarterly_operating_margin_pct"),
        ("operating_income", "full_year_operating_margin_pct"),
    ]

    x = np.arange(len(metrics))
    width = 0.35

    for i, label in enumerate(labels_list):
        vals = [companies[label].get(s, {}).get(k, 0) for s, k in keys]
        bars = ax.bar(x + i * width, vals, width, label=label, color=COLORS.get(label, "#999"))
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{val:.1f}%", ha="center", va="bottom", fontsize=9)

    ax.set_ylabel("%")
    ax.set_title("Operating Margin Comparison")
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(metrics)
    ax.legend()

    save(fig, out_dir, "2_margin_comparison")


# --- Chart 3: EPS Comparison ---
def chart_eps(companies: dict, out_dir: Path):
    fig, ax = plt.subplots(figsize=(8, 5))

    labels_list = list(companies.keys())
    metrics = ["Q EPS Basic", "Q EPS Diluted", "FY EPS Basic", "FY EPS Diluted"]
    keys = [
        ("net_income_and_eps", "quarterly_eps_basic"),
        ("net_income_and_eps", "quarterly_eps_diluted"),
        ("net_income_and_eps", "full_year_eps_basic"),
        ("net_income_and_eps", "full_year_eps_diluted"),
    ]

    x = np.arange(len(metrics))
    width = 0.35

    for i, label in enumerate(labels_list):
        vals = [companies[label].get(s, {}).get(k, 0) for s, k in keys]
        bars = ax.bar(x + i * width, vals, width, label=label, color=COLORS.get(label, "#999"))
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"${val:.2f}", ha="center", va="bottom", fontsize=9)

    ax.set_ylabel("$ per share")
    ax.set_title("Earnings Per Share Comparison")
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(metrics)
    ax.legend()

    save(fig, out_dir, "3_eps_comparison")


# --- Chart 4: Segment Revenue Mix (one pie per company) ---
def chart_segment_mix(companies: dict, out_dir: Path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for idx, (label, data) in enumerate(companies.items()):
        ax = axes[idx]
        segments = data.get("segments", [])
        names = [s["segment_name"] for s in segments]
        sales = [s.get("quarterly_net_sales", 0) for s in segments]
        colors = SEGMENT_PALETTE[:len(names)]

        wedges, texts, autotexts = ax.pie(
            sales, labels=names, autopct="%1.1f%%", colors=colors,
            textprops={"fontsize": 9}
        )
        for at in autotexts:
            at.set_fontsize(8)
        ax.set_title(f"{label} Revenue Mix")

    fig.suptitle("Segment Revenue Mix (Most Recent Quarter)", fontsize=13, y=1.02)
    save(fig, out_dir, "4_segment_revenue_mix")


# --- Chart 5: Segment Operating Margin ---
def chart_segment_margin(companies: dict, out_dir: Path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)

    for idx, (label, data) in enumerate(companies.items()):
        ax = axes[idx]
        segments = data.get("segments", [])
        names = [s["segment_name"] for s in segments]
        margins = [s.get("quarterly_operating_margin_pct", 0) for s in segments]
        colors = SEGMENT_PALETTE[:len(names)]

        bars = ax.barh(names, margins, color=colors)
        for bar, val in zip(bars, margins):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                    f"{val:.1f}%", va="center", fontsize=9)

        ax.set_xlabel("Operating Margin %")
        ax.set_title(f"{label}")
        ax.invert_yaxis()

    fig.suptitle("Segment Operating Margins (Most Recent Quarter)", fontsize=13, y=1.02)
    fig.tight_layout()
    save(fig, out_dir, "5_segment_operating_margin")


# --- Chart 6: OCF vs CapEx vs FCF ---
def chart_cash_flow(companies: dict, out_dir: Path):
    fig, ax = plt.subplots(figsize=(10, 5))

    labels_list = list(companies.keys())
    x = np.arange(len(labels_list))
    width = 0.25

    ocf = [companies[l]["cash_flow"]["operating_cash_flow"] for l in labels_list]
    capex = [companies[l]["capex"]["total_capex"] for l in labels_list]
    fcf = [companies[l]["cash_flow"]["free_cash_flow"] for l in labels_list]

    bars1 = ax.bar(x - width, ocf, width, label="Operating Cash Flow", color="#2196F3")
    bars2 = ax.bar(x, capex, width, label="CapEx", color="#F44336")
    bars3 = ax.bar(x + width, fcf, width, label="Free Cash Flow", color="#4CAF50")

    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"${bar.get_height():,.0f}", ha="center", va="bottom", fontsize=8)

    ax.set_ylabel("$M")
    ax.set_title("Cash Flow: Operating CF vs CapEx vs Free CF")
    ax.set_xticks(x)
    ax.set_xticklabels(labels_list)
    ax.legend()
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    save(fig, out_dir, "6_cash_flow_comparison")


# --- Chart 7: Liquidity - Cash & Securities vs Debt ---
def chart_liquidity(companies: dict, out_dir: Path):
    fig, ax = plt.subplots(figsize=(8, 5))

    labels_list = list(companies.keys())
    x = np.arange(len(labels_list))
    width = 0.35

    total_cash = []
    total_debt = []
    for l in labels_list:
        liq = companies[l].get("cash_flow_and_liquidity", {}).get("liquidity", {})
        cash = (liq.get("cash_and_equivalents", 0) or 0) + \
               (liq.get("current_marketable_securities", 0) or 0) + \
               (liq.get("non_current_marketable_securities", 0) or 0)
        debt = liq.get("total_debt", 0) or 0
        total_cash.append(cash)
        total_debt.append(debt)

    bars1 = ax.bar(x - width / 2, total_cash, width, label="Cash & Securities", color="#4CAF50")
    bars2 = ax.bar(x + width / 2, total_debt, width, label="Total Debt", color="#F44336")

    for bars in [bars1, bars2]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"${bar.get_height():,.0f}", ha="center", va="bottom", fontsize=8)

    ax.set_ylabel("$M")
    ax.set_title("Liquidity: Cash & Securities vs Total Debt")
    ax.set_xticks(x)
    ax.set_xticklabels(labels_list)
    ax.legend()
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    save(fig, out_dir, "7_liquidity_comparison")


# --- Chart 8: Guidance Range (Amazon only) ---
def chart_guidance(companies: dict, out_dir: Path):
    amzn = companies.get("Amazon", {})
    fg = amzn.get("forward_guidance", {})
    if not fg.get("has_guidance"):
        return

    fig, ax = plt.subplots(figsize=(8, 4))

    metrics = ["Revenue", "Operating Income"]
    lows = [fg.get("revenue_low", 0), fg.get("operating_income_low", 0)]
    highs = [fg.get("revenue_high", 0), fg.get("operating_income_high", 0)]
    mids = [(l + h) / 2 for l, h in zip(lows, highs)]
    ranges = [(h - l) / 2 for l, h in zip(lows, highs)]

    y = np.arange(len(metrics))
    ax.barh(y, mids, xerr=ranges, height=0.4, color="#FF9900", capsize=8, alpha=0.8)

    for i, (lo, hi) in enumerate(zip(lows, highs)):
        ax.text(lo - 500, i, f"${lo:,.0f}", va="center", ha="right", fontsize=9)
        ax.text(hi + 500, i, f"${hi:,.0f}", va="center", ha="left", fontsize=9)

    ax.set_yticks(y)
    ax.set_yticklabels(metrics)
    ax.set_xlabel("$M")
    ax.set_title(f"Amazon Forward Guidance — {fg.get('guidance_period', '')}")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    save(fig, out_dir, "8_guidance_range")


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "v8"
    out_dir = ROOT / "charts" / version
    out_dir.mkdir(parents=True, exist_ok=True)

    companies = load_data(version)
    print(f"Generating charts for {version} → charts/{version}/")

    chart_revenue(companies, out_dir)
    chart_margins(companies, out_dir)
    chart_eps(companies, out_dir)
    chart_segment_mix(companies, out_dir)
    chart_segment_margin(companies, out_dir)
    chart_cash_flow(companies, out_dir)
    chart_liquidity(companies, out_dir)
    chart_guidance(companies, out_dir)

    print(f"\nDone. Insert these into your Google Sheets tabs via Insert > Image.")


if __name__ == "__main__":
    main()
