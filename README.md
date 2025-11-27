# Portfolio in Peril – Cardiff Edition

A lightweight, continuous 40-minute trading simulation built with Flask. One laptop hosts the server, and teams join from their browsers to allocate portfolios across global asset buckets while reacting to macro news rounds inspired by a Black Monday-style crash and recovery. The UI mimics a Bloomberg terminal with live news tape, flow-sensitive market moves, and quick-read charts.

## Features
- Eight predefined macro stages spread across a 40-minute continuous tape with narrative news and per-asset returns.
- Terminal-style play screen with live news stream plus random crashwire snippets for atmosphere.
- Interactive canvas charts for NAV path, every underlying security, and a crowd-flow adjusted market index that responds to aggregate allocations and trade shouts.
- Teams register once and play from their browser; allocations are normalized server-side.
- Voice-driven trade flow: players buzz a trade, shout it to the host, and the host accepts/rejects on the admin wallboard; fills nudge market impact.
- Admin controls to oversee the tape (auto-advancing on the 40-minute clock), apply returns manually if desired, reset the game, and view the private leaderboard.
- Leaderboard ranking by current NAV with round-by-round NAV history.

## Requirements
- Python 3.10+
- `flask` (install via `pip install flask`)

## How to run
1. Install dependencies: `pip install flask` (or `pip install -r requirements.txt` if you add one).
2. Optional: set an admin password via environment variable, e.g. `export ADMIN_PASSWORD=cardiffquant`.
3. Start the server from the repo root: `python app.py` (binds to `0.0.0.0:5000` by default). Set `FLASK_PORT=7000` (or another free port) if 5000 is occupied; the app will auto-fall back to the next port if it detects the address is already in use. The tape runs continuously for ~40 minutes; scenario beats auto-advance on that clock.
4. On the host laptop, open `http://localhost:<port>/admin` for controls and `http://localhost:<port>/` for the player landing page. Keep `/admin` projected for the “wallboard” with news, charts, and trade tape.
5. Other players on the same network join via `http://<host-ip>:<port>`—no login beyond a team name. They cannot see other teams’ NAV or orders; only the host wallboard is multi-team.

## Gameplay guide
- **Register:** Teams enter a unique name on the landing page; the session stores the team identity.
- **Allocate:** On `/play`, review the current round’s news and enter weights for any assets (non-negative numbers). Blank fields count as zero. Weights are normalized to sum to 1; if all are zero the submission is rejected. Every security shows a live mini-chart.
- **Buzz a trade:** On `/play`, pick side/asset/price, hit the buzzer, and shout the trade to the host. The host accepts/rejects on `/admin`; fills add a temporary market impact.
- **One submission per round:** After submitting for a round, the form is locked until the admin advances.
- **Advancing rounds:** Stages auto-advance on the 40-minute clock; the admin can also nudge “Advance” to sync everyone. Teams that did not submit carry forward their last allocation (or default to 100% CASH for the first round).
- **Flow impact:** When the admin advances, the engine adjusts returns by crowding (weights above/below an even split can boost or drag returns, capped at ±6%), and updates the live market index chart and news tape.
- **Scoring:** NAV starts at 100.0 and compounds each round using submitted (or carried) weights and the round’s returns. After round 8, view final standings at `/leaderboard`.
- **Privacy:** Players only see their own NAV and orders. The leaderboard is host-only during the session; project `/admin` if you want spectators to follow along.

## Configuration notes
- Asset list, round names, narratives, and returns are defined in `game_config.py`. Adjust these for different scenarios or return assumptions.
- Stateful data (teams, allocations, NAVs, current round, trades) is kept in memory; restart the process to clear state or use the Reset button on `/admin`.

## Troubleshooting
- If you see “team name taken”, pick a unique name; sessions are cookie-based, so use separate browser profiles for multiple teams on one machine.
- Ensure all players can reach the host’s IP on the chosen port (default 5000); firewalls may need to allow local network access. If you see “address already in use,” either stop the conflicting process (macOS users: AirPlay Receiver sometimes uses 5000) or rerun with `FLASK_PORT=<free_port>`.
