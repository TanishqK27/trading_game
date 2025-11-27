from __future__ import annotations

import math
import random
from datetime import datetime
from typing import Dict, List

# Core asset universe
ASSETS: List[str] = [
    "US_EQ",
    "EU_EQ",
    "ASIA_EQ",
    "US_GOV",
    "EU_GOV",
    "EM_DEBT",
    "GLOBAL_RE",
    "CASH",
]

ASSET_FRIENDLY_NAMES: Dict[str, str] = {
    "US_EQ": "US Equities",
    "EU_EQ": "European Equities",
    "ASIA_EQ": "Asian & EM Equities",
    "US_GOV": "US Government Bonds",
    "EU_GOV": "Euro Government Bonds",
    "EM_DEBT": "Emerging Market Debt",
    "GLOBAL_RE": "Global Real Estate",
    "CASH": "Cash",
}


# Baseline daily drifts and volatilities (per simulated day)
ASSET_BASELINES: Dict[str, Dict[str, float]] = {
    "US_EQ": {"drift": 0.0006, "vol": 0.012},
    "EU_EQ": {"drift": 0.00055, "vol": 0.0115},
    "ASIA_EQ": {"drift": 0.0007, "vol": 0.013},
    "US_GOV": {"drift": 0.00015, "vol": 0.0025},
    "EU_GOV": {"drift": 0.00012, "vol": 0.0028},
    "EM_DEBT": {"drift": 0.0004, "vol": 0.0065},
    "GLOBAL_RE": {"drift": 0.00035, "vol": 0.0095},
    "CASH": {"drift": 0.00005, "vol": 0.0},
}


# Macro shock timeline (seconds into the 40-minute run)
# Each event can deliver immediate shocks plus decay thereafter.
CURRENT_YEAR = datetime.utcnow().year
EVENTS: List[Dict[str, object]] = [
    {
        "time_offset": 3 * 60,  # 3 minutes in
        "headline": "Flash PMI miss sparks growth worries; desks lean risk-off.",
        "impact": {"US_EQ": -0.012, "EU_EQ": -0.01, "ASIA_EQ": -0.014, "US_GOV": 0.004, "EU_GOV": 0.0035},
    },
    {
        "time_offset": 10 * 60,  # 10 minutes
        "headline": "Systematic deleveraging wave hits futures; liquidity thins across the board.",
        "impact": {"US_EQ": -0.025, "EU_EQ": -0.021, "ASIA_EQ": -0.028, "GLOBAL_RE": -0.02, "EM_DEBT": -0.015},
    },
    {
        "time_offset": 17 * 60,  # 17 minutes
        "headline": "Central bank surprise statement pledges intraday liquidity backstop.",
        "impact": {"US_EQ": 0.018, "EU_EQ": 0.016, "ASIA_EQ": 0.02, "US_GOV": -0.003, "EU_GOV": -0.0025},
    },
    {
        "time_offset": 24 * 60,  # 24 minutes
        "headline": "Mega fund rotates billions into cash; cross-asset vols pop again.",
        "impact": {"US_EQ": -0.02, "EU_EQ": -0.017, "ASIA_EQ": -0.022, "GLOBAL_RE": -0.018, "EM_DEBT": -0.012},
    },
    {
        "time_offset": 31 * 60,  # 31 minutes
        "headline": "Stabilisation flows and buy-the-dip algos narrow losses into the close.",
        "impact": {"US_EQ": 0.014, "EU_EQ": 0.012, "ASIA_EQ": 0.016, "GLOBAL_RE": 0.01},
    },
    {
        "time_offset": 37 * 60,  # 37 minutes
        "headline": "Late-session squeeze accelerates as shorts scramble to cover.",
        "impact": {"US_EQ": 0.022, "EU_EQ": 0.018, "ASIA_EQ": 0.024, "GLOBAL_RE": 0.013, "EM_DEBT": 0.01},
    },
]


def random_live_headlines() -> List[str]:
    base = [
        "Desk chatter: vol sellers widen collars as intraday swings accelerate.",
        "FX basis tics wider; funding desks report patchy USD liquidity.",
        "Energy futures gap on inventory chatter; dealers cite shallow books.",
        "Large pension rebalancing pinged; equity futures briefly lift.",
        "Credit ETFs trade at discounts, prompting arb flows and hedges.",
        "CTA trend signals flip; systematic supply hits index futures.",
        "Tech megacaps drift as traders fade overnight headlines.",
        "Financials lag peers on capital ratio chatter; CDS indices gap.",
        "Real estate screens amber as rate path reprices intraday.",
        "Macro pod shops skew short beta while discretionary funds nibble dips.",
    ]
    random.shuffle(base)
    return base[:8]


# Used by API for filler when tape is quiet
LIVE_NEWS_SNIPPETS: List[str] = random_live_headlines()
