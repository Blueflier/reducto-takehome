"""
Ground truth from Segment Information tables (in millions).

Amazon segments (Q4 2024 vs Q4 2023):
  North America: sales=115,586 (prior=105,514) | op income=9,256
  International:  sales=43,420  (prior=40,243)  | op income=1,315
  AWS:            sales=28,786  (prior=24,204)  | op income=10,632

  Revenue mix (Q4 2024): North America=62%, International=23%, AWS=15%

Apple segments (Q3 2024 vs Q3 2023, from Note 11):
  Americas:             sales=37,678 (prior=35,383) | op income=15,209
  Europe:               sales=21,884 (prior=20,205) | op income=9,170
  Greater China:        sales=14,728 (prior=15,758) | op income=5,562
  Japan:                sales=5,097  (prior=4,821)  | op income=2,544
  Rest of Asia Pacific: sales=6,390  (prior=5,630)  | op income=2,610
"""

import pytest

TOLERANCE = 0.02  # 2% tolerance for computed fields


def find_segment(segments, name):
    """Find a segment by name (case-insensitive, partial match)."""
    name_lower = name.lower()
    for seg in segments:
        if name_lower in seg.get("segment_name", "").lower():
            return seg
    pytest.fail(f"Segment '{name}' not found in: {[s.get('segment_name') for s in segments]}")


# --- Amazon Segments ---

class TestAmazonSegmentCount:
    def test_has_three_segments(self, amzn):
        segments = amzn["segments"]
        names = set(s["segment_name"].lower().replace(" segment", "") for s in segments)
        assert "north america" in names
        assert "international" in names
        assert "aws" in names


class TestAmazonNorthAmerica:
    def test_quarterly_net_sales(self, amzn):
        seg = find_segment(amzn["segments"], "North America")
        assert seg["quarterly_net_sales"] == 115586

    def test_quarterly_prior_year_net_sales(self, amzn):
        seg = find_segment(amzn["segments"], "North America")
        assert seg["quarterly_prior_year_net_sales"] == 105514

    def test_quarterly_operating_income(self, amzn):
        seg = find_segment(amzn["segments"], "North America")
        assert seg["quarterly_operating_income"] == 9256


class TestAmazonInternational:
    def test_quarterly_net_sales(self, amzn):
        seg = find_segment(amzn["segments"], "International")
        assert seg["quarterly_net_sales"] == 43420

    def test_quarterly_prior_year_net_sales(self, amzn):
        seg = find_segment(amzn["segments"], "International")
        assert seg["quarterly_prior_year_net_sales"] == 40243

    def test_quarterly_operating_income(self, amzn):
        seg = find_segment(amzn["segments"], "International")
        assert seg["quarterly_operating_income"] == 1315


class TestAmazonAWS:
    def test_quarterly_net_sales(self, amzn):
        seg = find_segment(amzn["segments"], "AWS")
        assert seg["quarterly_net_sales"] == 28786

    def test_quarterly_prior_year_net_sales(self, amzn):
        seg = find_segment(amzn["segments"], "AWS")
        assert seg["quarterly_prior_year_net_sales"] == 24204

    def test_quarterly_operating_income(self, amzn):
        seg = find_segment(amzn["segments"], "AWS")
        assert seg["quarterly_operating_income"] == 10632


# --- Apple Segments ---

class TestAppleSegmentCount:
    def test_has_five_segments(self, aapl):
        segments = aapl["segments"]
        names = set(s["segment_name"].lower() for s in segments)
        assert "americas" in names
        assert "europe" in names
        assert "greater china" in names
        assert "japan" in names
        assert "rest of asia pacific" in names


class TestAppleAmericas:
    def test_quarterly_net_sales(self, aapl):
        seg = find_segment(aapl["segments"], "Americas")
        assert seg["quarterly_net_sales"] == 37678

    def test_quarterly_prior_year_net_sales(self, aapl):
        seg = find_segment(aapl["segments"], "Americas")
        assert seg["quarterly_prior_year_net_sales"] == 35383

    def test_quarterly_operating_income(self, aapl):
        seg = find_segment(aapl["segments"], "Americas")
        assert seg["quarterly_operating_income"] == 15209


class TestAppleEurope:
    def test_quarterly_net_sales(self, aapl):
        seg = find_segment(aapl["segments"], "Europe")
        assert seg["quarterly_net_sales"] == 21884

    def test_quarterly_operating_income(self, aapl):
        seg = find_segment(aapl["segments"], "Europe")
        assert seg["quarterly_operating_income"] == 9170


class TestAppleGreaterChina:
    def test_quarterly_net_sales(self, aapl):
        seg = find_segment(aapl["segments"], "Greater China")
        assert seg["quarterly_net_sales"] == 14728

    def test_quarterly_prior_year_net_sales(self, aapl):
        seg = find_segment(aapl["segments"], "Greater China")
        assert seg["quarterly_prior_year_net_sales"] == 15758

    def test_quarterly_operating_income(self, aapl):
        seg = find_segment(aapl["segments"], "Greater China")
        assert seg["quarterly_operating_income"] == 5562


class TestAppleJapan:
    def test_quarterly_net_sales(self, aapl):
        seg = find_segment(aapl["segments"], "Japan")
        assert seg["quarterly_net_sales"] == 5097


class TestAppleRestOfAsiaPacific:
    def test_quarterly_net_sales(self, aapl):
        seg = find_segment(aapl["segments"], "Rest of Asia Pacific")
        assert seg["quarterly_net_sales"] == 6390
