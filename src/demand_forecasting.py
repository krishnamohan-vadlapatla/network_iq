"""
NetworkIQ — Demand Forecasting Module
=======================================
Tiered forecasting: XGBoost (A-class), Holt-Winters (B-class), SMA (C-class).
"""

import numpy as np
import pandas as pd
from typing import Dict, List
import warnings
warnings.filterwarnings("ignore")

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
except ImportError:
    ExponentialSmoothing = None

try:
    from xgboost import XGBRegressor
except ImportError:
    XGBRegressor = None


class DemandForecaster:
    """Tiered demand forecasting engine with cost-per-decision tracking."""

    def __init__(self, config: dict):
        self.config = config
        self.horizon = config.get("optimization", {}).get("planning_horizon_weeks", 12)
        self.seed = config.get("random_seed", 42)
        self.models: Dict[str, str] = {}
        reasoning = config.get("reasoning", {})
        self.cost_per_forecast = {
            "A": reasoning.get("a_class_cost", 3.50),
            "B": reasoning.get("b_class_cost", 0.30),
            "C": reasoning.get("c_class_cost", 0.10),
        }

    def forecast_all(self, weekly_demand: pd.DataFrame, sku_classes: Dict[str, str],
                     regions: List[str]) -> pd.DataFrame:
        """Generate forecasts for all SKU-region combinations."""
        results = []
        for product_id in weekly_demand["Product_ID"].unique():
            sku_class = sku_classes.get(product_id, "C")
            for region in regions:
                mask = (weekly_demand["Product_ID"] == product_id) & (weekly_demand["Region"] == region)
                series = weekly_demand.loc[mask].sort_values(["Year", "Week"])
                if len(series) < 4:
                    forecast = self._forecast_sma(series, product_id, region, model_name="mean_fallback")
                elif sku_class == "A" and XGBRegressor is not None:
                    forecast = self._forecast_xgboost(series, product_id, region)
                elif sku_class == "B" and ExponentialSmoothing is not None:
                    forecast = self._forecast_holtwinters(series, product_id, region)
                else:
                    forecast = self._forecast_sma(series, product_id, region)
                for rec in forecast:
                    rec["SKU_Class"] = sku_class
                    rec["Cost_Per_Decision"] = self.cost_per_forecast.get(sku_class, 0.10)
                results.extend(forecast)
        return pd.DataFrame(results)

    def _forecast_xgboost(self, series: pd.DataFrame, pid: str, region: str) -> List[dict]:
        demand = series["Weekly_Demand"].values.astype(float)
        if len(demand) < 8:
            return self._forecast_sma(series, pid, region, model_name="xgb_fallback")
        X, y = [], []
        w = 4
        for i in range(w, len(demand)):
            X.append([demand[i-1], demand[i-2], np.mean(demand[i-w:i]),
                       np.std(demand[i-w:i]), i % 52, demand[i-1] - demand[i-2]])
            y.append(demand[i])
        model = XGBRegressor(n_estimators=50, max_depth=4, learning_rate=0.1,
                             random_state=self.seed, verbosity=0)
        model.fit(np.array(X), np.array(y))
        results, last = [], list(demand[-w:])
        for wa in range(1, self.horizon + 1):
            feat = [last[-1], last[-2] if len(last)>=2 else last[-1],
                    np.mean(last[-w:]), np.std(last[-w:]) if len(last)>=2 else 0,
                    (len(demand)+wa)%52, last[-1]-(last[-2] if len(last)>=2 else last[-1])]
            pred = max(0, float(model.predict(np.array([feat]))[0]))
            ci = pred * 0.20
            results.append({"Product_ID": pid, "Region": region, "Week_Ahead": wa,
                           "Forecast": round(pred,2), "Lower_CI": round(max(0,pred-ci),2),
                           "Upper_CI": round(pred+ci,2), "Model_Used": "xgboost"})
            last.append(pred)
        self.models[f"{pid}_{region}"] = "xgboost"
        return results

    def _forecast_holtwinters(self, series: pd.DataFrame, pid: str, region: str) -> List[dict]:
        demand = series["Weekly_Demand"].values.astype(float)
        if len(demand) < 8:
            return self._forecast_sma(series, pid, region, model_name="hw_fallback")
        try:
            model = ExponentialSmoothing(demand, trend="add", seasonal=None,
                                        initialization_method="estimated").fit(optimized=True)
            fv = model.forecast(self.horizon)
            res_std = np.std(demand - model.fittedvalues)
            results = []
            for wa in range(1, self.horizon+1):
                pred = max(0, float(fv[wa-1]))
                ci = 1.65 * res_std * np.sqrt(wa)
                results.append({"Product_ID": pid, "Region": region, "Week_Ahead": wa,
                               "Forecast": round(pred,2), "Lower_CI": round(max(0,pred-ci),2),
                               "Upper_CI": round(pred+ci,2), "Model_Used": "holt_winters"})
            self.models[f"{pid}_{region}"] = "holt_winters"
            return results
        except Exception:
            return self._forecast_sma(series, pid, region, model_name="hw_fallback")

    def _forecast_sma(self, series: pd.DataFrame, pid: str, region: str,
                      window: int = 4, model_name: str = "sma") -> List[dict]:
        demand = series["Weekly_Demand"].values.astype(float)
        if len(demand) == 0:
            avg, std = 0.0, 0.0
        elif len(demand) < window:
            avg = float(np.mean(demand))
            std = float(np.std(demand)) if len(demand) > 1 else avg * 0.3
        else:
            avg = float(np.mean(demand[-window:]))
            std = float(np.std(demand[-window:]))
        ci = 1.65 * std
        return [{"Product_ID": pid, "Region": region, "Week_Ahead": w,
                 "Forecast": round(max(0, avg), 2), "Lower_CI": round(max(0, avg-ci), 2),
                 "Upper_CI": round(avg+ci, 2), "Model_Used": model_name}
                for w in range(1, self.horizon+1)]

    def get_forecast_summary(self, forecasts: pd.DataFrame) -> dict:
        return {
            "total_forecasts": len(forecasts),
            "unique_skus": forecasts["Product_ID"].nunique(),
            "model_distribution": forecasts["Model_Used"].value_counts().to_dict(),
            "avg_forecast": round(forecasts["Forecast"].mean(), 2),
        }
