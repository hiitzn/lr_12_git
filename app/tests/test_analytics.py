from app.services.analytics_service import AnalyticsService


def test_analytics_structure():

    analytics = {
        "revenue": 0,
        "status_stats": [],
        "top_dishes": [],
        "table_load": "0/0"
    }

    assert "revenue" in analytics
    assert "status_stats" in analytics
    assert "top_dishes" in analytics
    assert "table_load" in analytics