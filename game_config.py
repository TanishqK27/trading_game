"""Game configuration for the Open Outcry trading game."""

SESSION_DURATION_SECONDS = 40 * 60  # 40 minutes live tape
TICK_SECONDS = 3  # price updates every 3 seconds

INSTRUMENTS = [
    {"code": "EQ_FUT", "name": "Equity Index Future", "base_price": 100.0},
    {"code": "OIL", "name": "Crude Oil", "base_price": 72.0},
    {"code": "GOLD", "name": "Gold", "base_price": 1950.0},
    {"code": "RATE", "name": "10Y Rate Future", "base_price": 112.0},
    {"code": "FX", "name": "GBP/USD", "base_price": 1.26},
]

# News events fire over the 40-minute tape. They influence the drift and volatility for a period.
NEWS_EVENTS = [
    {"second": 60, "headline": "Opening bell: floor clerks brace for heavy flows as risk sentiment wobbles.", "shock": {"EQ_FUT": -0.3, "RATE": 0.15}},
    {"second": 6 * 60, "headline": "Energy desk reports refinery outage; crude bids lift across pits.", "shock": {"OIL": 1.1}},
    {"second": 10 * 60, "headline": "Central bank governor hints at emergency meeting; rates swing wider.", "shock": {"RATE": -0.8, "EQ_FUT": 0.25}},
    {"second": 16 * 60, "headline": "Gold sees safe-haven demand after macro fund dumps risk.", "shock": {"GOLD": 0.7, "EQ_FUT": -0.5}},
    {"second": 22 * 60, "headline": "Cross-asset volatility spikes; locals shout for wider markets.", "shock": {"EQ_FUT": -0.9, "OIL": -0.4}},
    {"second": 28 * 60, "headline": "Rate stabilization whispers calm nerves; curve tightens.", "shock": {"RATE": 0.9, "EQ_FUT": 0.35}},
    {"second": 34 * 60, "headline": "Late-session short covering squeezes equity futures and FX.", "shock": {"EQ_FUT": 1.2, "FX": 0.4}},
]

# Default cash for each team
STARTING_CASH = 1_000_000.0

# Impact factor for large trades. Applied as (qty / IMPACT_SIZE) * impact_factor on price percent move.
IMPACT_SIZE = 500_000  # nominal size equivalent for 1% move
IMPACT_FACTOR = 0.015

