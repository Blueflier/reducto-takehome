"""
Ground truth for operational KPIs.

Amazon has rich supplemental metrics:
  - WW paid units YoY growth: 11%
  - WW seller unit mix: 62%
  - Employees: 1,556,000
  We test that at least some of these are captured.

Apple's 10-Q has no supplemental KPI table.
  We test that the array is empty or very small.
"""


def find_kpi(kpis, keyword):
    """Find a KPI by keyword in metric_name (case-insensitive)."""
    keyword_lower = keyword.lower()
    for kpi in kpis:
        if keyword_lower in kpi.get("metric_name", "").lower():
            return kpi
    return None


class TestAmazonKPIs:
    def test_has_kpis(self, amzn):
        kpis = amzn["key_business_metrics"]["operational_kpis"]
        assert len(kpis) >= 2

    def test_has_employee_metric(self, amzn):
        kpis = amzn["key_business_metrics"]["operational_kpis"]
        emp = find_kpi(kpis, "employee")
        assert emp is not None
        assert "1,556,000" in emp["current_value"] or "1556000" in emp["current_value"]

    def test_has_shipping_or_units_metric(self, amzn):
        """At least one of shipping costs, paid units, or seller mix is captured."""
        kpis = amzn["key_business_metrics"]["operational_kpis"]
        found = (
            find_kpi(kpis, "shipping") is not None
            or find_kpi(kpis, "paid unit") is not None
            or find_kpi(kpis, "seller") is not None
        )
        assert found


class TestAppleKPIs:
    def test_minimal_kpis(self, aapl):
        kpis = aapl["key_business_metrics"]["operational_kpis"]
        # Apple's 10-Q has no supplemental KPI table
        assert len(kpis) <= 3
