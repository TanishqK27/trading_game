# Open Outcry Trading Game

A hosted, browser-based simulation of an open outcry trading pit. Players grab a badge, shout orders, and watch prices move from news, flow, and their own size. Everything runs locally on a single Flask server.

## Features
- **40-minute continuous session** with price ticks every 3 seconds and headline-driven shocks.
- **Order book + tape**: limit and market orders, automatic matching, price impact for large clips.
- **Live charts**: each player sees their NAV curve and price boards; host sees full books and leaderboard.
- **Bloomberg-style skin**: dark background with orange highlights for quick scanning.
- **News tape**: scheduled macro headlines that influence drift/volatility.

## Quick start
1. `pip install flask`
2. Optional: `export ADMIN_PASSWORD=hostsecret` and `export FLASK_SECRET=random`
3. `python app.py` (set `FLASK_PORT` to change the port)
4. Host: open `http://localhost:5000/admin` for controls and the wallboard.
5. Players: navigate to `http://<host-ip>:5000/`, enter a team name, and proceed to the pit.

## How it works
- **Badges**: players register a team name; state is tracked in memory.
- **Orders**: choose instrument, side, size, and optional limit price. Market orders match immediately; limits rest on the book until crossed.
- **Matching & impact**: crossed prices trade; fills update cash/positions and nudge prices based on size to mimic floor impact.
- **News**: timed headlines add temporary drift to instruments (e.g., crude outage, central bank whispers).
- **P&L**: NAV = cash + marked-to-market positions. Each player sees only their own NAV/positions; admins see all teams.
- **Session control**: admins can pause/resume/reset. The tape stops automatically after 40 minutes.

## Tips for hosting
- Project the `/admin` page as the wallboard so everyone can see the depth, tape, and standings.
- Encourage players to shout before pressing the buy/sell button to keep the open outcry vibe.
- Reset between rounds of play via the admin panel.

## Customisation
- Instruments, start prices, news events, and impact factors live in `game_config.py`.
- Adjust `SESSION_DURATION_SECONDS` and `TICK_SECONDS` for different timings.

