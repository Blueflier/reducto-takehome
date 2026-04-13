"""
Ground truth from Consolidated Statements of Cash Flows, financing activities (in millions).

Amazon (FY 2024):
  Repayments of long-term debt: 9,182
  Repayments of short-term debt: 5,060
  Principal repayments of finance leases: 2,043
  Cash paid for operating leases: 12,341 (supplemental section)

Apple (9M 2024):
  Repayments of term debt: 7,400
  Repayments of commercial paper, net: 2,985
  No finance leases reported
  No operating lease payments reported in cash flow supplemental
"""


class TestAmazonDebtRepayments:
    def test_long_term_debt(self, amzn):
        assert amzn["cash_flow_and_liquidity"]["debt_repayments"]["long_term_debt_repayments"] == 9182

    def test_short_term_debt(self, amzn):
        assert amzn["cash_flow_and_liquidity"]["debt_repayments"]["short_term_debt_repayments"] == 5060


class TestAmazonLeaseObligations:
    def test_finance_lease_repayments(self, amzn):
        assert amzn["cash_flow_and_liquidity"]["lease_obligations"]["finance_lease_principal_repayments"] == 2043

    def test_operating_lease_payments(self, amzn):
        assert amzn["cash_flow_and_liquidity"]["lease_obligations"]["operating_lease_payments"] == 12341


class TestAppleDebtRepayments:
    def test_long_term_debt(self, aapl):
        assert aapl["cash_flow_and_liquidity"]["debt_repayments"]["long_term_debt_repayments"] == 7400

    def test_short_term_debt(self, aapl):
        assert aapl["cash_flow_and_liquidity"]["debt_repayments"]["short_term_debt_repayments"] == 2985


class TestAppleLeaseObligations:
    def test_finance_lease_repayments(self, aapl):
        assert aapl["cash_flow_and_liquidity"]["lease_obligations"]["finance_lease_principal_repayments"] == 0

    def test_operating_lease_payments(self, aapl):
        assert aapl["cash_flow_and_liquidity"]["lease_obligations"]["operating_lease_payments"] == 0
