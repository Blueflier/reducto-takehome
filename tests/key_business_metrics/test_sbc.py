"""
Ground truth for stock-based compensation (in millions).

Amazon (from Supplemental Business Metrics table):
  Total SBC: Q4 2024=4,995 | Q4 2023=6,319
  Full year (from cash flow stmt): FY 2024=22,011 | FY 2023=24,023

Apple (from Note 9 Share-Based Compensation table):
  SBC expense: Q3 2024=2,869 | Q3 2023=2,617
  9M 2024=8,830 | 9M 2023=8,208
"""


class TestAmazonSBC:
    def test_quarterly_sbc(self, amzn):
        assert amzn["key_business_metrics"]["stock_based_compensation"]["quarterly_sbc"] == 4995

    def test_quarterly_prior_year_sbc(self, amzn):
        assert amzn["key_business_metrics"]["stock_based_compensation"]["quarterly_prior_year_sbc"] == 6319

    def test_full_year_sbc(self, amzn):
        assert amzn["key_business_metrics"]["stock_based_compensation"]["full_year_sbc"] == 22011

    def test_full_year_prior_year_sbc(self, amzn):
        assert amzn["key_business_metrics"]["stock_based_compensation"]["full_year_prior_year_sbc"] == 24023


class TestAppleSBC:
    def test_quarterly_sbc(self, aapl):
        assert aapl["key_business_metrics"]["stock_based_compensation"]["quarterly_sbc"] == 2869

    def test_quarterly_prior_year_sbc(self, aapl):
        assert aapl["key_business_metrics"]["stock_based_compensation"]["quarterly_prior_year_sbc"] == 2617

    def test_full_year_sbc(self, aapl):
        assert aapl["key_business_metrics"]["stock_based_compensation"]["full_year_sbc"] == 8830

    def test_full_year_prior_year_sbc(self, aapl):
        assert aapl["key_business_metrics"]["stock_based_compensation"]["full_year_prior_year_sbc"] == 8208
