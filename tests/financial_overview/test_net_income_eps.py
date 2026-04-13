"""
Ground truth from Consolidated Statements of Operations tables.

Amazon (in millions, except per share):
  Net income:   Q4 2024=20,004 | FY 2024=59,248
  Basic EPS:    Q4 2024=$1.90  | FY 2024=$5.66
  Diluted EPS:  Q4 2024=$1.86  | FY 2024=$5.53

Apple (in millions, except per share):
  Net income:   Q3 2024=21,448 | 9M 2024=79,000
  Basic EPS:    Q3 2024=$1.40  | 9M 2024=$5.13
  Diluted EPS:  Q3 2024=$1.40  | 9M 2024=$5.11
"""


class TestAmazonNetIncomeEPS:
    def test_quarterly_net_income(self, amzn):
        assert amzn["net_income_and_eps"]["quarterly_net_income"] == 20004

    def test_quarterly_eps_basic(self, amzn):
        assert amzn["net_income_and_eps"]["quarterly_eps_basic"] == 1.90

    def test_quarterly_eps_diluted(self, amzn):
        assert amzn["net_income_and_eps"]["quarterly_eps_diluted"] == 1.86

    def test_full_year_net_income(self, amzn):
        assert amzn["net_income_and_eps"]["full_year_net_income"] == 59248

    def test_full_year_eps_basic(self, amzn):
        assert amzn["net_income_and_eps"]["full_year_eps_basic"] == 5.66

    def test_full_year_eps_diluted(self, amzn):
        assert amzn["net_income_and_eps"]["full_year_eps_diluted"] == 5.53


class TestAppleNetIncomeEPS:
    def test_quarterly_net_income(self, aapl):
        assert aapl["net_income_and_eps"]["quarterly_net_income"] == 21448

    def test_quarterly_eps_basic(self, aapl):
        assert aapl["net_income_and_eps"]["quarterly_eps_basic"] == 1.40

    def test_quarterly_eps_diluted(self, aapl):
        assert aapl["net_income_and_eps"]["quarterly_eps_diluted"] == 1.40

    def test_full_year_net_income(self, aapl):
        assert aapl["net_income_and_eps"]["full_year_net_income"] == 79000

    def test_full_year_eps_basic(self, aapl):
        assert aapl["net_income_and_eps"]["full_year_eps_basic"] == 5.13

    def test_full_year_eps_diluted(self, aapl):
        assert aapl["net_income_and_eps"]["full_year_eps_diluted"] == 5.11
