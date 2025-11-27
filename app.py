"""
Portfolio in Peril – Continuous Tape Edition

How to run:
1. pip install flask
2. export ADMIN_PASSWORD=cardiffquant (or set your own) and optionally export FLASK_SECRET.
3. python app.py (defaults to port 5000; set FLASK_PORT to override)
4. Host laptop opens http://localhost:<port>/admin and http://localhost:<port>/.
5. Other players on the same network open http://<host-ip>:<port>.
"""
from __future__ import annotations

import os
import random
from typing import Dict

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from game_config import ASSET_FRIENDLY_NAMES, ASSETS, LIVE_NEWS_SNIPPETS
from models import GameState

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "devsecret")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "cardiffquant")
SESSION_DURATION_SECONDS = 40 * 60
TICK_SECONDS = 3

GAME_STATE = GameState(total_duration_seconds=SESSION_DURATION_SECONDS, tick_seconds=TICK_SECONDS)


def sync_state():
    GAME_STATE.sync_to_time()


def get_team_from_session():
    team_name = session.get("team_name")
    if team_name and team_name in GAME_STATE.teams:
        return GAME_STATE.teams[team_name]
    return None


@app.route("/", methods=["GET", "POST"])
def index():
    sync_state()
    team = get_team_from_session()
    if request.method == "POST":
        team_name = request.form.get("team_name", "").strip()
        if not team_name:
            flash("Please enter a team name.", "error")
            return render_template("index.html")
        try:
            GAME_STATE.register_team(team_name)
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("index.html")
        session["team_name"] = team_name
        flash("You are live on the tape — head to the Play tab.", "success")
        return redirect(url_for("play"))

    if team:
        return redirect(url_for("play"))
    return render_template("index.html")


@app.route("/play", methods=["GET", "POST"])
def play():
    sync_state()
    team = get_team_from_session()
    if not team:
        flash("Please register your team first.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        weights: Dict[str, float] = {}
        total = 0.0
        for asset in ASSETS:
            raw = request.form.get(asset)
            if raw is None or raw == "":
                continue
            try:
                val = float(raw)
            except ValueError:
                flash(f"Invalid number for {asset}.", "error")
                return redirect(url_for("play"))
            if val < 0:
                flash("Weights must be non-negative.", "error")
                return redirect(url_for("play"))
            weights[asset] = val
            total += val
        if total <= 0:
            flash("Provide at least one positive weight.", "error")
            return redirect(url_for("play"))
        try:
            GAME_STATE.update_allocation(team.name, weights)
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("play"))
        flash("Allocation refreshed — watch your chart respond.", "success")
        return redirect(url_for("play"))

    return render_template(
        "play.html",
        team=team,
        nav_history=team.nav_history,
        total_seconds_left=GAME_STATE.total_seconds_left,
        assets=ASSETS,
        asset_names=ASSET_FRIENDLY_NAMES,
        assets_meta=[{"code": code, "name": ASSET_FRIENDLY_NAMES.get(code, code)} for code in ASSETS],
    )


@app.post("/trade_request")
def trade_request():
    team = get_team_from_session()
    if not team:
        flash("Please register before requesting a trade.", "error")
        return redirect(url_for("index"))

    asset = request.form.get("asset", "US_EQ")
    side = request.form.get("side", "long")
    price = request.form.get("price", "mkt")
    note = request.form.get("note", "")
    try:
        GAME_STATE.add_trade_request(team.name, asset, side, price, note)
        flash("Trade yelled to host. Wait for fill/reject.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("play"))


@app.route("/admin", methods=["GET", "POST"])
def admin():
    sync_state()
    authorized = session.get("is_admin", False)
    provided_password = request.values.get("password")
    if provided_password:
        if provided_password == ADMIN_PASSWORD:
            session["is_admin"] = True
            authorized = True
            flash("Admin access granted.", "success")
        else:
            flash("Incorrect password.", "error")

    if not authorized:
        return render_template("admin.html", authorized=False)

    if request.method == "POST":
        action = request.form.get("action")
        if action == "reset":
            GAME_STATE.reset()
            flash("Simulation reset.", "success")
        elif action == "accept_trade":
            trade_id = request.form.get("trade_id", "")
            try:
                GAME_STATE.accept_trade(trade_id)
                flash(f"Trade {trade_id} accepted and applied to flows.", "success")
            except ValueError as exc:
                flash(str(exc), "error")
        elif action == "reject_trade":
            trade_id = request.form.get("trade_id", "")
            try:
                GAME_STATE.reject_trade(trade_id)
                flash(f"Trade {trade_id} rejected.", "info")
            except ValueError as exc:
                flash(str(exc), "error")
        return redirect(url_for("admin"))

    return render_template(
        "admin.html",
        authorized=True,
        game_state=GAME_STATE,
        assets=ASSETS,
        asset_names=ASSET_FRIENDLY_NAMES,
    )


@app.route("/leaderboard")
def leaderboard():
    sync_state()
    authorized = session.get("is_admin", False)
    teams_sorted = sorted(GAME_STATE.teams.values(), key=lambda t: t.current_nav, reverse=True)
    return render_template(
        "leaderboard.html",
        teams=teams_sorted if authorized else [get_team_from_session()] if get_team_from_session() else [],
        game_state=GAME_STATE,
        authorized=authorized,
    )


@app.route("/api/state")
def api_state():
    sync_state()
    team = get_team_from_session()
    authorized = session.get("is_admin", False)

    payload = {
        "is_finished": GAME_STATE.is_finished,
        "total_seconds_left": GAME_STATE.total_seconds_left,
        "market_index_history": GAME_STATE.market_index_history,
        "asset_index_histories": GAME_STATE.asset_index_histories,
        "news_feed": GAME_STATE.news_feed[-60:],
        "total_teams": len(GAME_STATE.teams),
    }

    if authorized:
        payload["pending_trades"] = [t for t in GAME_STATE.trade_requests if t.get("status") == "pending"]
        payload["trade_tape"] = GAME_STATE.trade_requests[-60:]
        payload["teams"] = [
            {"name": t.name, "nav": t.current_nav, "nav_history": t.nav_history, "allocation": t.allocation}
            for t in GAME_STATE.teams.values()
        ]
    else:
        payload["trade_tape_count"] = len(GAME_STATE.trade_requests)

    if team:
        payload["team"] = {"name": team.name, "nav_history": team.nav_history, "allocation": team.allocation}

    if LIVE_NEWS_SNIPPETS:
        payload["random_news"] = random.sample(LIVE_NEWS_SNIPPETS, k=min(12, len(LIVE_NEWS_SNIPPETS)))

    return jsonify(payload)


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port_env = os.getenv("FLASK_PORT") or os.getenv("PORT") or "5000"
    try:
        port = int(port_env)
    except ValueError:
        port = 5000

    try:
        app.run(host=host, port=port, debug=False)
    except OSError as exc:
        if getattr(exc, "errno", None) == 98:
            alt_port = port + 1
            print(f"Port {port} is busy. Falling back to {alt_port}. Set FLASK_PORT to choose a port explicitly.")
            app.run(host=host, port=alt_port, debug=False)
        else:
            raise
