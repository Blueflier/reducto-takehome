"""
Ground truth from Consolidated Statements of Operations tables (in millions).

Amazon (AMZN-Q4-2024-Earnings-Release.pdf):
  Table header: "(in millions, except per share data)"
  Total net sales row: Q4 2023=169,961 | Q4 2024=187,792 | FY 2023=574,785 | FY 2024=637,959

Apple (_10-Q-Q3-2024-As-Filed.pdf):
  Table header: "(In millions, except number of shares...)"
  Total net sales row: Q3 2024=85,777 | Q3 2023=81,797 | 9M 2024=296,105 | 9M 2023=293,787
"""

import pytest

TOLERANCE = 0.01  # allow 1% tolerance on computed percentages


class TestAmazonNetSales:
    def test_quarterly_sales(self, amzn):
        assert amzn["total_net_sales"]["quarterly_sales"] == 187792

    def test_quarterly_prior_year_sales(self, amzn):
        assert amzn["total_net_sales"]["quarterly_prior_year_sales"] == 169961

    def test_quarterly_growth_pct(self, amzn):
        expected = (187792 - 169961) / 169961 * 100  # ~10.48%
        actual = amzn["total_net_sales"]["quarterly_growth_pct"]
        assert abs(actual - expected) / expected < TOLERANCE

    def test_full_year_sales(self, amzn):
        assert amzn["total_net_sales"]["full_year_sales"] == 637959

    def test_full_year_prior_year_sales(self, amzn):
        assert amzn["total_net_sales"]["full_year_prior_year_sales"] == 574785

    def test_full_year_growth_pct(self, amzn):
        expected = (637959 - 574785) / 574785 * 100  # ~10.99%
        actual = amzn["total_net_sales"]["full_year_growth_pct"]
        assert abs(actual - expected) / expected < TOLERANCE


class TestAppleNetSales:
    def test_quarterly_sales(self, aapl):
        assert aapl["total_net_sales"]["quarterly_sales"] == 85777

    def test_quarterly_prior_year_sales(self, aapl):
        assert aapl["total_net_sales"]["quarterly_prior_year_sales"] == 81797

    def test_quarterly_growth_pct(self, aapl):
        expected = (85777 - 81797) / 81797 * 100  # ~4.86%
        actual = aapl["total_net_sales"]["quarterly_growth_pct"]
        assert abs(actual - expected) / expected < TOLERANCE

    def test_full_year_sales(self, aapl):
        assert aapl["total_net_sales"]["full_year_sales"] == 296105

    def test_full_year_prior_year_sales(self, aapl):
        assert aapl["total_net_sales"]["full_year_prior_year_sales"] == 293787

    def test_full_year_growth_pct(self, aapl):
        expected = (296105 - 293787) / 293787 * 100  # ~0.79%
        actual = aapl["total_net_sales"]["full_year_growth_pct"]
        assert abs(actual - expected) / expected < TOLERANCE
