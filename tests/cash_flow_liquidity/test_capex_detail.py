"""
Ground truth from Consolidated Statements of Cash Flows (in millions).

Amazon:
  Purchases of property and equipment (FY 2024): 82,999
  Finance lease additions (FY 2024): 854  (supplemental: "Property and equipment acquired under finance leases")
  Proceeds from property and equipment sales (FY 2024): 5,341

Apple (9M 2024):
  Payments for acquisition of property, plant and equipment: 6,539
  No finance leases reported
  No asset sale proceeds reported separately
"""


class TestAmazonCapexDetail:
    def test_purchases_of_property_and_equipment(self, amzn):
        assert amzn["cash_flow_and_liquidity"]["capital_expenditures"]["purchases_of_property_and_equipment"] == 82999

    def test_finance_lease_additions(self, amzn):
        assert amzn["cash_flow_and_liquidity"]["capital_expenditures"]["finance_lease_additions"] == 854

    def test_proceeds_from_asset_sales(self, amzn):
        assert amzn["cash_flow_and_liquidity"]["capital_expenditures"]["proceeds_from_asset_sales"] == 5341


class TestAppleCapexDetail:
    def test_purchases_of_property_and_equipment(self, aapl):
        assert aapl["cash_flow_and_liquidity"]["capital_expenditures"]["purchases_of_property_and_equipment"] == 6539

    def test_finance_lease_additions(self, aapl):
        assert aapl["cash_flow_and_liquidity"]["capital_expenditures"]["finance_lease_additions"] == 0

    def test_proceeds_from_asset_sales(self, aapl):
        assert aapl["cash_flow_and_liquidity"]["capital_expenditures"]["proceeds_from_asset_sales"] == 0
