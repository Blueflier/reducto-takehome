"""
Ground truth from the Financial Guidance section of each document.

Amazon (Q1 2025 Guidance, from "First Quarter 2025 Guidance" section):
  has_guidance: True
  period: Q1 2025
  Revenue: $151.0B - $155.5B → 151000 - 155500 in millions
  Revenue growth: 5% - 9%
  Operating income: $14.0B - $18.0B → 14000 - 18000 in millions
  FX impact: "unfavorable impact of approximately $2.1 billion, or 150 basis points"
  Other: Leap year comp ($1.5B in Q1 2024), no acquisitions/restructurings assumed

Apple:
  has_guidance: False (Apple does not provide quarterly guidance)
"""

import pytest


class TestAmazonGuidance:
    def test_has_guidance(self, amzn):
        assert amzn["forward_guidance"]["has_guidance"] is True

    def test_guidance_period(self, amzn):
        period = amzn["forward_guidance"]["guidance_period"]
        assert "Q1" in period and "2025" in period

    def test_revenue_low(self, amzn):
        assert amzn["forward_guidance"]["revenue_low"] == 151000

    def test_revenue_high(self, amzn):
        assert amzn["forward_guidance"]["revenue_high"] == 155500

    def test_revenue_growth_low(self, amzn):
        assert amzn["forward_guidance"]["revenue_growth_low_pct"] == 5

    def test_revenue_growth_high(self, amzn):
        assert amzn["forward_guidance"]["revenue_growth_high_pct"] == 9

    def test_operating_income_low(self, amzn):
        assert amzn["forward_guidance"]["operating_income_low"] == 14000

    def test_operating_income_high(self, amzn):
        assert amzn["forward_guidance"]["operating_income_high"] == 18000

    def test_fx_impact_amount(self, amzn):
        assert amzn["forward_guidance"]["fx_impact_amount"] == 2100

    def test_fx_impact_bps(self, amzn):
        assert amzn["forward_guidance"]["fx_impact_bps"] == 150


class TestAppleNoGuidance:
    def test_has_guidance(self, aapl):
        assert aapl["forward_guidance"]["has_guidance"] is False

    def test_revenue_low_null(self, aapl):
        assert aapl["forward_guidance"].get("revenue_low") is None

    def test_operating_income_low_null(self, aapl):
        assert aapl["forward_guidance"].get("operating_income_low") is None
