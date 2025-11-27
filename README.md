# Portfolio in Peril – Cardiff Edition

A Bloomberg-coloured, 40-minute continuous trading simulation built with Flask. One laptop hosts; everyone else joins from a browser. The tape ticks every 3 seconds with synthetic markets that react to macro headlines and crowd flow. Players see only their own P&L; the host wallboard shows everything.

## Features
- Continuous clock: 40 minutes of simulated “year” trading with a 3-second tick (roughly a day per tick). No rounds.
- Live charts: canvas-driven paths for every asset, a market index, and each team’s NAV (private to them). Host wallboard aggregates the top NAV.
- News flow: scheduled macro events plus ambient desk chatter create a scrolling ticker; big headlines hit prices immediately then decay.
- Flow-aware pricing: allocations and accepted trade “yells” push prices via a crowding/skew factor with decay.
- Shout-to-host trades: players press BUY/SELL, shout the price to the host, and the host accepts/rejects on `/admin`; fills move the tape.
- Privacy: teams cannot see other teams’ P&L; only the host/admin sees multi-team standings and trade tape.
- Bloomberg style: black/orange theme, compact grids, and projector-ready wallboard.

## Requirements
- Python 3.10+
- `flask` (install via `pip install flask`)

## How to run
1. Install dependencies: `pip install flask` (or add a requirements file and install from it).
2. Optional: set an admin password via environment variable, e.g. `export ADMIN_PASSWORD=cardiffquant`. You can also set `FLASK_SECRET` for the session key.
3. Start the server from the repo root: `python app.py`. Defaults to `0.0.0.0:5000`; set `FLASK_PORT=7000` (or another free port) if needed. If the port is busy, the server falls back to the next one and prints a hint.
4. Host laptop opens `http://localhost:<port>/admin` (for the wallboard) and `http://localhost:<port>/` (player landing). Keep `/admin` projected on the whiteboard.
5. Other players join via `http://<host-ip>:<port>` on the same network. They only need a team name.

## Gameplay guide
- **Register:** Enter a unique team name on `/`. Cookie-based identity; use separate browser profiles for multiple teams on one machine.
- **Rebalance anytime:** On `/play`, set weights for each asset (non-negative). Blanks are zero. We normalise to 100% and apply from the next tick onward.
- **Buzz a trade:** Hit BUY (green) or SELL (red), shout the trade to the host. Host accepts/rejects on `/admin`; accepted trades tilt prices with a temporary impact.
- **Live charts:** NAV and asset paths update every ~3 seconds (one simulated day). News ticker blends scheduled macro shocks and random desk chatter.
- **Wallboard:** The host sees pending trades, recent fills, news, market index, and per-asset mini charts. Only the host sees full rankings at `/leaderboard`.
- **Session end:** After ~40 minutes the clock naturally expires; prices stop updating. Hit Reset on `/admin` to start over.

## Configuration notes
- Asset list, baseline drifts/vols, and macro event timeline live in `game_config.py`.
- State is in-memory; restarting the process or pressing Reset clears everything.

## Troubleshooting
- “Address already in use”: stop the conflicting process or set `FLASK_PORT` to a free port; the app will try the next port automatically.
- “Team name taken”: choose a different name; names are case-insensitive.
- Connectivity: ensure players can reach the host IP/port on the LAN; check firewalls if pages do not load.
