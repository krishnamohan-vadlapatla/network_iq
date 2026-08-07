"""
NetworkIQ — Self-Check Module
===============================
Validates the final optimization plan against business goals.
Flags regressions and infeasible outcomes before submission.
"""

from typing import Dict, List


class SelfChecker:
    """Automated self-check against business goals."""

    def __init__(self, config: dict):
        self.config = config
        opt = config.get("optimization", {})
        self.service_target = opt.get("service_level_target", 0.95)

    def check_plan(self, plan_metrics: dict, baseline_metrics: dict = None,
                   transfers: list = None, capacity: dict = None) -> dict:
        """
        Validate the plan against business goals.
        Returns pass/fail per criterion with explanations.
        """
        checks = []

        # 1. Service level check
        sl = plan_metrics.get("service_level", 0)
        checks.append({
            "criterion": "Service Level",
            "target": f">= {self.service_target:.0%}",
            "actual": f"{sl:.2%}",
            "passed": sl >= self.service_target,
            "explanation": f"Service level {sl:.2%} {'meets' if sl >= self.service_target else 'BELOW'} target {self.service_target:.0%}."
        })

        # 2. Cost guardrail compliance
        if transfers:
            violations = [t for t in transfers if not t.get("Passes_Cost_Guardrail", True)]
            approved_violations = [t for t in violations if t.get("Status") != "rejected_guardrail"]
            checks.append({
                "criterion": "Cost Guardrail Compliance",
                "target": "0 violations in approved transfers",
                "actual": f"{len(approved_violations)} violations",
                "passed": len(approved_violations) == 0,
                "explanation": f"{len(violations)} transfers failed cost guardrail; {len(approved_violations)} were still approved."
            })

        # 3. Capacity feasibility
        if capacity:
            infeasible = plan_metrics.get("capacity_violations", 0)
            checks.append({
                "criterion": "Capacity Feasibility",
                "target": "0 violations",
                "actual": f"{infeasible} violations",
                "passed": infeasible == 0,
                "explanation": f"{'All locations within capacity.' if infeasible == 0 else f'{infeasible} locations exceed capacity — INFEASIBLE.'}"
            })

        # 4. Improvement over baseline (if available)
        if baseline_metrics:
            bl_cost = baseline_metrics.get("total_cost", 0)
            plan_cost = plan_metrics.get("total_cost", 0)
            improved = plan_cost <= bl_cost
            pct = ((bl_cost - plan_cost) / bl_cost * 100) if bl_cost > 0 else 0
            checks.append({
                "criterion": "Cost Improvement vs Baseline",
                "target": "Total cost <= baseline",
                "actual": f"₹{plan_cost:,.0f} vs ₹{bl_cost:,.0f} ({pct:+.1f}%)",
                "passed": improved,
                "explanation": f"Plan {'reduces' if improved else 'INCREASES'} total cost by {abs(pct):.1f}% vs classical baseline."
            })

            bl_sl = baseline_metrics.get("service_level", 0)
            sl_improved = sl >= bl_sl
            checks.append({
                "criterion": "Service Level vs Baseline",
                "target": "Service level >= baseline",
                "actual": f"{sl:.2%} vs {bl_sl:.2%}",
                "passed": sl_improved,
                "explanation": f"Service level {'improved' if sl_improved else 'DECLINED'} vs baseline."
            })

        # 5. In-stock rate at high-velocity locations
        a_instock = plan_metrics.get("a_class_instock_rate", 1.0)
        checks.append({
            "criterion": "A-Class In-Stock Rate",
            "target": ">= 98%",
            "actual": f"{a_instock:.1%}",
            "passed": a_instock >= 0.98,
            "explanation": f"A-class SKU availability {'meets' if a_instock >= 0.98 else 'BELOW'} 98% target."
        })

        overall_pass = all(c["passed"] for c in checks)

        return {
            "overall_status": "PASSED" if overall_pass else "FAILED",
            "checks": checks,
            "total_checks": len(checks),
            "passed_checks": sum(1 for c in checks if c["passed"]),
            "failed_checks": sum(1 for c in checks if not c["passed"]),
        }
