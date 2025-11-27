# Portfolio in Peril – Cardiff Edition

A lightweight multi-round trading simulation built with Flask. One laptop hosts the server, and teams join from their browsers to allocate portfolios across global asset buckets while reacting to macro news rounds inspired by a Black Monday-style crash and recovery. The UI mimics a Bloomberg terminal with live news tape, flow-sensitive market moves, and quick-read charts.

## Features
- Eight predefined macro rounds with narrative news and per-asset returns.
- Terminal-style play screen with live news stream plus random crashwire snippets for atmosphere.
- Interactive canvas charts for NAV path, every underlying security, and a crowd-flow adjusted market index that responds to aggregate allocations and trade shouts.
- Teams register once and play from their browser; allocations are normalized server-side.
- Voice-driven trade flow: players buzz a trade, shout it to the host, and the host accepts/rejects on the admin wallboard; fills nudge market impact.
- Admin controls to advance rounds, apply returns (with carry-forward logic), reset the game, and view the leaderboard.
- Leaderboard ranking by current NAV with round-by-round NAV history.

## Requirements
- Python 3.10+
- `flask` (install via `pip install flask`)

## How to run
1. Install dependencies: `pip install flask` (or `pip install -r requirements.txt` if you add one).
2. Optional: set an admin password via environment variable, e.g. `export ADMIN_PASSWORD=cardiffquant`.
3. Start the server from the repo root: `python app.py` (binds to `0.0.0.0:5000`). Each round is timed at ~5 minutes, yielding ~40 minutes of total play.
4. On the host laptop, open `http://localhost:5000/admin` for controls and `http://localhost:5000/` for the player landing page. Keep `/admin` projected for the “wallboard” with news, charts, and trade tape.
5. Other players on the same network join via `http://<host-ip>:5000`—no login beyond a team name.

## Gameplay guide
- **Register:** Teams enter a unique name on the landing page; the session stores the team identity.
- **Allocate:** On `/play`, review the current round’s news and enter weights for any assets (non-negative numbers). Blank fields count as zero. Weights are normalized to sum to 1; if all are zero the submission is rejected. Every security shows a live mini-chart.
- **Buzz a trade:** On `/play`, pick side/asset/price, hit the buzzer, and shout the trade to the host. The host accepts/rejects on `/admin`; fills add a temporary market impact.
- **One submission per round:** After submitting for a round, the form is locked until the admin advances.
- **Advancing rounds:** The admin advances rounds from `/admin`. Teams that did not submit carry forward their last allocation (or default to 100% CASH for the first round).
- **Flow impact:** When the admin advances, the engine adjusts returns by crowding (weights above/below an even split can boost or drag returns, capped at ±6%), and updates the live market index chart and news tape.
- **Scoring:** NAV starts at 100.0 and compounds each round using submitted (or carried) weights and the round’s returns. After round 8, view final standings at `/leaderboard`.

## Configuration notes
- Asset list, round names, narratives, and returns are defined in `game_config.py`. Adjust these for different scenarios or return assumptions.
- Stateful data (teams, allocations, NAVs, current round, trades) is kept in memory; restart the process to clear state or use the Reset button on `/admin`.

## Troubleshooting
- If you see “team name taken”, pick a unique name; sessions are cookie-based, so use separate browser profiles for multiple teams on one machine.
- Ensure all players can reach the host’s IP on port 5000; firewalls may need to allow local network access.
