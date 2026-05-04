"""
Supply Chain Risk Monitor — Prophet Forecasting Module
Forecasts per-supplier risk scores using Meta's Prophet.

y(t) = g(t) + s(t) + h(t) + ε(t)
  g: piecewise linear trend with auto changepoints
  s: weekly + optional yearly seasonality
  h: user-defined supply chain disruption events (port closures, audits, etc.)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SupplierRiskSeries:
    """Daily risk-score time series for a single supplier.

    risk_score: 0–100 composite (e.g. weighted sum of SLA breaches,
                temperature deviations, lead-time overruns).
    disruption_events: optional list of known shock dates with labels,
                       used as custom Prophet holidays.
    """
    supplier: str
    dates: list[str]          # ISO 8601 strings, e.g. "2024-01-15"
    risk_scores: list[float]  # same length as dates
    disruption_events: list[dict[str, Any]] = field(default_factory=list)
    # each dict: {"label": str, "ds": str, "lower_window": int, "upper_window": int}
    country_holidays: str | None = None  # e.g. "US", "IN", "TW"


@dataclass
class ForecastResult:
    supplier: str
    forecasts: list[dict[str, Any]]       # yhat / yhat_lower / yhat_upper per day
    components: dict[str, str]
    metadata: dict[str, Any]


# ---------------------------------------------------------------------------
# Core forecast function
# ---------------------------------------------------------------------------

def forecast_supplier_risk(
    series: SupplierRiskSeries,
    forecast_days: int = 90,
    changepoint_prior_scale: float = 0.05,
    seasonality_mode: str = "additive",
    run_cv: bool = True,
    cv_horizon: str = "30 days",
) -> ForecastResult:
    """Fit a Prophet model to a supplier's daily risk score and forecast forward.

    Parameters
    ----------
    series:
        Historical risk data for one supplier.
    forecast_days:
        How many calendar days ahead to predict.
    changepoint_prior_scale:
        Flexibility of trend changepoints (default 0.05; increase for fast-
        moving suppliers, decrease for stable baselines).
    seasonality_mode:
        "additive" (default) or "multiplicative". Use "multiplicative" when
        risk amplitude grows proportionally with the trend level.
    run_cv:
        Whether to run Prophet's rolling-window cross-validation for MAPE.
        Disable for very short series (< 60 days) or fast batch runs.
    cv_horizon:
        Prophet cross-validation horizon string, e.g. "30 days".
    """
    df = _to_prophet_df(series)
    _validate(df, series.supplier)

    holidays_df = _build_holidays_df(series)

    m = Prophet(
        growth="linear",
        changepoint_prior_scale=changepoint_prior_scale,
        seasonality_mode=seasonality_mode,
        yearly_seasonality=len(df) >= 365,
        weekly_seasonality=True,
        holidays=holidays_df if not holidays_df.empty else None,
    )

    if series.country_holidays:
        m.add_country_holidays(country_name=series.country_holidays)

    m.fit(df)

    future = m.make_future_dataframe(periods=forecast_days)
    fc = m.predict(future)

    # Clip to [0, 100] — risk scores are bounded
    for col in ("yhat", "yhat_lower", "yhat_upper"):
        fc[col] = fc[col].clip(0, 100)

    mape = None
    if run_cv and len(df) >= 60:
        mape = _run_cross_validation(m, df, cv_horizon)

    forecasts = _extract_future_rows(fc, len(df))
    components = _summarise_components(fc)

    return ForecastResult(
        supplier=series.supplier,
        forecasts=forecasts,
        components=components,
        metadata={
            "mape": round(mape, 4) if mape is not None else None,
            "training_days": len(df),
            "forecast_days": forecast_days,
            "changepoint_prior_scale": changepoint_prior_scale,
            "seasonality_mode": seasonality_mode,
            "n_changepoints_detected": int(
                (m.params["delta"].mean(axis=0) != 0).sum()
            ),
        },
    )


# ---------------------------------------------------------------------------
# Batch helper
# ---------------------------------------------------------------------------

def forecast_portfolio(
    series_list: list[SupplierRiskSeries],
    forecast_days: int = 90,
    **kwargs,
) -> list[ForecastResult]:
    """Forecast risk for multiple suppliers in sequence."""
    return [
        forecast_supplier_risk(s, forecast_days=forecast_days, **kwargs)
        for s in series_list
    ]


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def result_to_dict(result: ForecastResult) -> dict[str, Any]:
    return {
        "supplier": result.supplier,
        "forecasts": result.forecasts,
        "components": result.components,
        "metadata": result.metadata,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_prophet_df(series: SupplierRiskSeries) -> pd.DataFrame:
    return pd.DataFrame({"ds": pd.to_datetime(series.dates), "y": series.risk_scores})


def _validate(df: pd.DataFrame, supplier: str) -> None:
    if len(df) < 14:
        raise ValueError(
            f"Supplier '{supplier}': need at least 14 data points, got {len(df)}"
        )
    if df["y"].isna().all():
        raise ValueError(f"Supplier '{supplier}': all risk scores are NaN")


def _build_holidays_df(series: SupplierRiskSeries) -> pd.DataFrame:
    if not series.disruption_events:
        return pd.DataFrame()
    rows = []
    for ev in series.disruption_events:
        rows.append(
            {
                "holiday": ev.get("label", "event"),
                "ds": pd.to_datetime(ev["ds"]),
                "lower_window": int(ev.get("lower_window", 0)),
                "upper_window": int(ev.get("upper_window", 1)),
            }
        )
    return pd.DataFrame(rows)


def _run_cross_validation(m: Prophet, df: pd.DataFrame, horizon: str) -> float:
    # initial = half the series; period = horizon
    initial_days = max(30, len(df) // 2)
    try:
        cv_df = cross_validation(
            m,
            initial=f"{initial_days} days",
            period=horizon,
            horizon=horizon,
            disable_tqdm=True,
        )
        perf = performance_metrics(cv_df, rolling_window=1)
        return float(perf["mape"].mean())
    except Exception:
        return None


def _extract_future_rows(fc: pd.DataFrame, n_train: int) -> list[dict[str, Any]]:
    future_fc = fc.iloc[n_train:].copy()
    return [
        {
            "ds": row["ds"].strftime("%Y-%m-%d"),
            "yhat": round(float(row["yhat"]), 2),
            "yhat_lower": round(float(row["yhat_lower"]), 2),
            "yhat_upper": round(float(row["yhat_upper"]), 2),
        }
        for _, row in future_fc.iterrows()
    ]


def _summarise_components(fc: pd.DataFrame) -> dict[str, str]:
    trend_start = fc["trend"].iloc[0]
    trend_end = fc["trend"].iloc[-1]
    direction = "upward" if trend_end > trend_start else "downward"
    pct = abs((trend_end - trend_start) / (trend_start + 1e-9)) * 100

    weekly_amp = (
        fc["weekly"].max() - fc["weekly"].min()
        if "weekly" in fc.columns
        else 0.0
    )

    return {
        "trend": f"{direction}_{pct:.1f}pct",
        "weekly_seasonality_amplitude": f"{weekly_amp:.2f}",
    }


# ---------------------------------------------------------------------------
# Demo / smoke test
# ---------------------------------------------------------------------------

def _generate_demo_series(supplier: str, n_days: int = 180, seed: int = 42) -> SupplierRiskSeries:
    rng = np.random.default_rng(seed)
    start = date(2024, 1, 1)
    dates = [(start + timedelta(days=i)).isoformat() for i in range(n_days)]

    # Base: slow upward trend + weekly pattern + noise
    t = np.arange(n_days)
    trend = 20 + 0.05 * t
    weekly = 5 * np.sin(2 * np.pi * t / 7)
    noise = rng.normal(0, 2, n_days)
    scores = np.clip(trend + weekly + noise, 0, 100).tolist()

    disruption_events = [
        {"label": "port_closure", "ds": "2024-04-01", "lower_window": 0, "upper_window": 3},
        {"label": "gdp_audit",    "ds": "2024-07-15", "lower_window": -1, "upper_window": 1},
    ]

    return SupplierRiskSeries(
        supplier=supplier,
        dates=dates,
        risk_scores=scores,
        disruption_events=disruption_events,
    )


if __name__ == "__main__":
    print("=== Supply Chain Risk Forecast (Prophet) ===\n")

    demo_series = _generate_demo_series("Acme Logistics", n_days=180)
    result = forecast_supplier_risk(
        demo_series,
        forecast_days=30,
        run_cv=True,
        cv_horizon="14 days",
    )

    print(f"Supplier : {result.supplier}")
    print(f"Metadata : {json.dumps(result.metadata, indent=2)}")
    print(f"Components: {result.components}")
    print(f"\nFirst 5 forecast rows:")
    for row in result.forecasts[:5]:
        print(f"  {row['ds']}  yhat={row['yhat']:5.1f}  "
              f"[{row['yhat_lower']:5.1f}, {row['yhat_upper']:5.1f}]")
