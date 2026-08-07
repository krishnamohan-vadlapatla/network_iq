"""
NetworkIQ — Demand Planning API Stub
=====================================
"""

class DemandPlanningApi:
    def submit_forecasts(self, forecasts: list) -> dict:
        return {"status": "success", "recorded": len(forecasts)}
