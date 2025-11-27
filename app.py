"""
Open Outcry Trading Game

How to run:
1. pip install flask
2. Optional: export ADMIN_PASSWORD=hostsecret and FLASK_SECRET for sessions
3. python app.py (defaults to port 5000; override via FLASK_PORT)
4. Host opens http://localhost:<port>/admin for controls and wallboard
5. Players join http://<host-ip>:<port>/ to register and enter the pit
"""
from __future__ import annotations

import os
from typing import Optional

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

from game_config import INSTRUMENTS, SESSION_DURATION_SECONDS, TICK_SECONDS
from models import GameState

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "devsecret")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "cardiffquant")

GAME_STATE = GameState()


def current_team_name() -> Optional[str]:
    name = session.get("team_name")
    if name and name in GAME_STATE.teams:
        return name
    return None


@app.route("/", methods=["GET", "POST"])
def index():
    team = current_team_name()
    if request.method == "POST":
        name = request.form.get("team_name", "").strip()
        try:
            GAME_STATE.register_team(name)
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("index.html")
        session["team_name"] = name
        flash("Badge printed. Step into the pit!", "success")
        return redirect(url_for("pit"))
    if team:
        return redirect(url_for("pit"))
    return render_template("index.html")


@app.route("/pit", methods=["GET", "POST"])
def pit():
    team_name = current_team_name()
    if not team_name:
        flash("Please register your badge first.", "error")
        return redirect(url_for("index"))
    if request.method == "POST":
        instrument = request.form.get("instrument", INSTRUMENTS[0]["code"])
        side = request.form.get("side", "buy")
        qty_raw = request.form.get("qty", "0")
        price_raw = request.form.get("price", "")
        limit_price = None
        try:
            qty = float(qty_raw)
        except ValueError:
            flash("Quantity must be a number.", "error")
            return redirect(url_for("pit"))
        if price_raw.strip():
            try:
                limit_price = float(price_raw)
            except ValueError:
                flash("Price must be numeric or left blank for market.", "error")
                return redirect(url_for("pit"))
        try:
            GAME_STATE.place_order(team_name, instrument, side, qty, limit_price)
            flash("Order shouted to the ring.", "success")
        except ValueError as exc:
            flash(str(exc), "error")
        return redirect(url_for("pit"))
    return render_template("pit.html", instruments=INSTRUMENTS)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    is_admin = session.get("is_admin", False)
    supplied = request.values.get("password")
    if supplied:
        if supplied == ADMIN_PASSWORD:
            session["is_admin"] = True
            is_admin = True
            flash("Admin granted.", "success")
        else:
            flash("Wrong password.", "error")
    if not is_admin:
        return render_template("admin.html", authorized=False)

    if request.method == "POST":
        action = request.form.get("action")
        if action == "reset":
            GAME_STATE.reset()
            flash("Session reset and cleared.", "success")
        elif action == "pause":
            GAME_STATE.active = False
            flash("Tape paused.", "info")
        elif action == "resume":
            if GAME_STATE.remaining > 0:
                GAME_STATE.active = True
                GAME_STATE.last_tick = GAME_STATE.start_time + GAME_STATE.elapsed
            flash("Tape resumed.", "success")
    return render_template("admin.html", authorized=True, instruments=INSTRUMENTS)


@app.route("/leaderboard")
def leaderboard():
    is_admin = session.get("is_admin", False)
    team_name = current_team_name()
    data = GAME_STATE.state_for_team(team_name if not is_admin else None, include_private=is_admin)
    teams = data.get("leaderboard", [])
    if not is_admin and team_name:
        teams = [entry for entry in teams if entry["team"] == team_name]
    return render_template("leaderboard.html", teams=teams, authorized=is_admin)


@app.route("/api/state")
def api_state():
    team_name = current_team_name()
    include_private = bool(session.get("is_admin", False))
    return jsonify(GAME_STATE.state_for_team(team_name, include_private=include_private))


if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.getenv("FLASK_PORT", 5000))
    try:
        app.run(host=host, port=port, debug=False)
    except OSError as exc:
        alt_port = port + 1
        print(f"Port {port} busy ({exc}). Trying {alt_port}.")
        app.run(host=host, port=alt_port, debug=False)

