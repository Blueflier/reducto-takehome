"""
Ground truth from Consolidated Statements of Operations tables (in millions).

Amazon: Operating income Q4 2024=21,203 | FY 2024=68,593
        Net sales       Q4 2024=187,792 | FY 2024=637,959
        Margin: Q4=11.29% | FY=10.75%

Apple:  Operating income Q3 2024=25,352 | 9M 2024=93,625
        Net sales        Q3 2024=85,777 | 9M 2024=296,105
        Margin: Q3=29.56% | 9M=31.62%
"""

TOLERANCE = 0.01


class TestAmazonOperatingIncome:
    def test_quarterly_operating_income(self, amzn):
        assert amzn["operating_income"]["quarterly_operating_income"] == 21203

    def test_quarterly_margin(self, amzn):
        expected = 21203 / 187792 * 100  # ~11.29%
        actual = amzn["operating_income"]["quarterly_operating_margin_pct"]
        assert abs(actual - expected) / expected < TOLERANCE

    def test_full_year_operating_income(self, amzn):
        assert amzn["operating_income"]["full_year_operating_income"] == 68593

    def test_full_year_margin(self, amzn):
        expected = 68593 / 637959 * 100  # ~10.75%
        actual = amzn["operating_income"]["full_year_operating_margin_pct"]
        assert abs(actual - expected) / expected < TOLERANCE


class TestAppleOperatingIncome:
    def test_quarterly_operating_income(self, aapl):
        assert aapl["operating_income"]["quarterly_operating_income"] == 25352

    def test_quarterly_margin(self, aapl):
        expected = 25352 / 85777 * 100  # ~29.56%
        actual = aapl["operating_income"]["quarterly_operating_margin_pct"]
        assert abs(actual - expected) / expected < TOLERANCE

    def test_full_year_operating_income(self, aapl):
        assert aapl["operating_income"]["full_year_operating_income"] == 93625

    def test_full_year_margin(self, aapl):
        expected = 93625 / 296105 * 100  # ~31.62%
        actual = aapl["operating_income"]["full_year_operating_margin_pct"]
        assert abs(actual - expected) / expected < TOLERANCE
