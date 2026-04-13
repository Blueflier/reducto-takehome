"""
Ground truth from Consolidated Balance Sheets, most recent period (in millions).

Amazon (Dec 31, 2024):
  Cash and cash equivalents: 78,779
  Marketable securities (current): 22,423
  Non-current marketable securities: not listed separately (in Other assets)
  Long-term debt: 52,623
  No short-term debt line item on balance sheet
  Total debt: 52,623

Apple (Jun 29, 2024):
  Cash and cash equivalents: 25,565
  Marketable securities (current): 36,236
  Marketable securities (non-current): 91,240
  Current term debt: 12,114
  Current commercial paper: 2,994
  Non-current term debt: 86,196
  Total debt: 12,114 + 2,994 + 86,196 = 101,304
"""


class TestAmazonLiquidity:
    def test_cash_and_equivalents(self, amzn):
        assert amzn["cash_flow_and_liquidity"]["liquidity"]["cash_and_equivalents"] == 78779

    def test_current_marketable_securities(self, amzn):
        assert amzn["cash_flow_and_liquidity"]["liquidity"]["current_marketable_securities"] == 22423

    def test_non_current_marketable_securities(self, amzn):
        # Amazon does not list non-current marketable securities separately
        assert amzn["cash_flow_and_liquidity"]["liquidity"]["non_current_marketable_securities"] == 0

    def test_total_debt(self, amzn):
        assert amzn["cash_flow_and_liquidity"]["liquidity"]["total_debt"] == 52623


class TestAppleLiquidity:
    def test_cash_and_equivalents(self, aapl):
        assert aapl["cash_flow_and_liquidity"]["liquidity"]["cash_and_equivalents"] == 25565

    def test_current_marketable_securities(self, aapl):
        assert aapl["cash_flow_and_liquidity"]["liquidity"]["current_marketable_securities"] == 36236

    def test_non_current_marketable_securities(self, aapl):
        assert aapl["cash_flow_and_liquidity"]["liquidity"]["non_current_marketable_securities"] == 91240

    def test_total_debt(self, aapl):
        # current term debt (12,114) + commercial paper (2,994) + non-current term debt (86,196)
        assert aapl["cash_flow_and_liquidity"]["liquidity"]["total_debt"] == 101304
