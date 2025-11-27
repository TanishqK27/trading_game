from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from models import Round

CURRENT_YEAR = datetime.utcnow().year

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

ROUNDS: List[Round] = [
    Round(
        index=1,
        name="Late-Cycle Boom",
        news=(
            f"{CURRENT_YEAR} tape opens strong with AI-capex euphoria; inflation is contained.\n"
            "Earnings surprises keep equities buoyant and credit spreads grind tighter as desks run light risk."
        ),
        returns={
            "US_EQ": 0.08,
            "EU_EQ": 0.07,
            "ASIA_EQ": 0.09,
            "US_GOV": 0.01,
            "EU_GOV": 0.008,
            "EM_DEBT": 0.055,
            "GLOBAL_RE": 0.06,
            "CASH": 0.005,
        },
    ),
    Round(
        index=2,
        name="Frothy Valuations",
        news=(
            "IPO pipeline is hot, margin debt climbs, and passive inflows overwhelm dealers.\n"
            "Analysts debate whether markets are priced for perfection while vol stays muted into the weekend."
        ),
        returns={
            "US_EQ": 0.06,
            "EU_EQ": 0.05,
            "ASIA_EQ": 0.07,
            "US_GOV": 0.0,
            "EU_GOV": -0.002,
            "EM_DEBT": 0.035,
            "GLOBAL_RE": 0.045,
            "CASH": 0.004,
        },
    ),
    Round(
        index=3,
        name="Black Monday Shock",
        news=(
            f"A sudden crash echoes 1987: algo hedges and CTA de-risking trigger a cascade ({CURRENT_YEAR} edition).\n"
            "Circuit breakers trip and liquidity dries up for hours before stabilising; screens glow red."
        ),
        returns={
            "US_EQ": -0.22,
            "EU_EQ": -0.18,
            "ASIA_EQ": -0.25,
            "US_GOV": 0.03,
            "EU_GOV": 0.025,
            "EM_DEBT": -0.12,
            "GLOBAL_RE": -0.16,
            "CASH": 0.002,
        },
    ),
    Round(
        index=4,
        name="Central Bank Rescue",
        news=(
            "Coordinated rate cuts, liquidity lines, and swap backstops calm nerves.\n"
            "Risk assets rebound while bond yields retrace the flight-to-quality move; vol sellers creep back."
        ),
        returns={
            "US_EQ": 0.14,
            "EU_EQ": 0.11,
            "ASIA_EQ": 0.16,
            "US_GOV": -0.01,
            "EU_GOV": -0.008,
            "EM_DEBT": 0.09,
            "GLOBAL_RE": 0.1,
            "CASH": 0.002,
        },
    ),
    Round(
        index=5,
        name="Inflation Scare",
        news=(
            "Commodity spikes and wage growth surprise.\n"
            "Bond markets reprice sharply higher yields while equities wobble."
        ),
        returns={
            "US_EQ": -0.04,
            "EU_EQ": -0.035,
            "ASIA_EQ": -0.05,
            "US_GOV": -0.02,
            "EU_GOV": -0.018,
            "EM_DEBT": -0.025,
            "GLOBAL_RE": -0.03,
            "CASH": 0.002,
        },
    ),
    Round(
        index=6,
        name="Eurozone Debt Jitters",
        news=(
            "Peripheral spreads widen as a mid-sized bank wobbles; ECB holds emergency presser.\n"
            "Safe havens catch a bid; EM is resilient thanks to reforms and cleaner balance sheets."
        ),
        returns={
            "US_EQ": -0.015,
            "EU_EQ": -0.03,
            "ASIA_EQ": 0.01,
            "US_GOV": 0.012,
            "EU_GOV": 0.009,
            "EM_DEBT": 0.018,
            "GLOBAL_RE": -0.01,
            "CASH": 0.002,
        },
    ),
    Round(
        index=7,
        name="Tech Renaissance",
        news=(
            "AI productivity stories fuel a growth rally.\n"
            "Capital expenditure rises, and credit markets reopen for issuers."
        ),
        returns={
            "US_EQ": 0.12,
            "EU_EQ": 0.08,
            "ASIA_EQ": 0.1,
            "US_GOV": -0.005,
            "EU_GOV": -0.003,
            "EM_DEBT": 0.04,
            "GLOBAL_RE": 0.065,
            "CASH": 0.002,
        },
    ),
    Round(
        index=8,
        name="Soft Landing or Stall?",
        news=(
            "Growth slows but avoids recession; earnings are mixed.\n"
            "Investors debate whether to lock in gains or stay risk-on into next year."
        ),
        returns={
            "US_EQ": 0.035,
            "EU_EQ": 0.03,
            "ASIA_EQ": 0.045,
            "US_GOV": 0.004,
            "EU_GOV": 0.003,
            "EM_DEBT": 0.02,
            "GLOBAL_RE": 0.025,
            "CASH": 0.002,
        },
    ),
]

LIVE_NEWS_SNIPPETS: List[str] = [
    "Circuit breakers halt trading on index futures as volatility surges.",
    "Rumours swirl of a sovereign wealth fund rotating billions into cash.",
    "Buyback desks pause programs; quants flag crowded momentum unwind.",
    "Dollar funding tightens intraday; cross-currency basis widens.",
    "Macro funds lean short duration as inflation whispers persist.",
    "Dealers widen bid/ask on equity ETFs; liquidity pockets vanish.",
    "Real money extends duration, pressing long-end yields lower.",
    "EM central bank hints at pre-emptive hikes to anchor FX.",
    "REITs catch a bid on yield-hunt flows despite equity turmoil.",
    "Energy majors signal capex restraint; crude slides on positioning.",
    "Vol-targeting strategies forced to de-risk, amplifying swings.",
]
