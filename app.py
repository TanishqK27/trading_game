"""
Portfolio in Peril – Cardiff Edition

How to run:
1. pip install flask
2. export ADMIN_PASSWORD=cardiffquant (or set your own) and optionally export FLASK_SECRET.
3. python app.py
4. Host laptop opens http://localhost:5000/admin and http://localhost:5000/.
5. Other players on the same network open http://<host-ip>:5000.
"""
from __future__ import annotations

import os
from typing import Dict

from flask import Flask, flash, redirect, render_template, request, session, url_for

from game_config import ASSETS, ASSET_FRIENDLY_NAMES, ROUNDS
from models import GameState

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "devsecret")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "cardiffquant")

# Initialize global game state
GAME_STATE = GameState(assets=ASSETS, rounds=ROUNDS)


def get_team_from_session():
    team_name = session.get("team_name")
    if team_name and team_name in GAME_STATE.teams:
        return GAME_STATE.teams[team_name]
    return None


@app.route("/", methods=["GET", "POST"])
def index():
    team = get_team_from_session()
    if request.method == "POST":
        team_name = request.form.get("team_name", "").strip()
        if not team_name:
            flash("Please enter a team name.", "error")
            return render_template("index.html")

        try:
            GAME_STATE.register_team(team_name)
        except ValueError as exc:  # duplicate or invalid
            flash(str(exc), "error")
            return render_template("index.html")

        session["team_name"] = team_name
        flash("Welcome aboard! Head to the Play page to submit allocations.", "success")
        return redirect(url_for("play"))

    if team:
        return redirect(url_for("play"))
    return render_template("index.html")


@app.route("/play", methods=["GET", "POST"])
def play():
    team = get_team_from_session()
    if not team:
        flash("Please register your team first.", "error")
        return redirect(url_for("index"))

    finished = GAME_STATE.is_finished
    current_round_index = min(GAME_STATE.current_round, GAME_STATE.num_rounds)
    current_round = (
        GAME_STATE.rounds[current_round_index - 1]
        if not finished and GAME_STATE.rounds
        else None
    )

    if request.method == "POST":
        if finished:
            flash("The game is finished. No more allocations accepted.", "error")
            return redirect(url_for("play"))

        if team.has_allocation(current_round_index):
            flash("You have already submitted for this round.", "info")
            return redirect(url_for("play"))

        weights: Dict[str, float] = {}
        sum_weights = 0.0
        for asset in ASSETS:
            raw = request.form.get(asset)
            if raw is None or raw == "":
                continue
            try:
                value = float(raw)
            except ValueError:
                flash(f"Invalid number for {asset}.", "error")
                return redirect(url_for("play"))
            if value < 0:
                flash("Weights must be non-negative.", "error")
                return redirect(url_for("play"))
            weights[asset] = value
            sum_weights += value

        if sum_weights <= 0:
            flash("Please provide at least one positive allocation.", "error")
            return redirect(url_for("play"))

        normalized = {asset: weight / sum_weights for asset, weight in weights.items()}
        try:
            GAME_STATE.record_allocation(team.name, current_round_index, normalized)
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("play"))

        flash("Allocation submitted for this round!", "success")
        return redirect(url_for("play"))

    submitted = not finished and team.has_allocation(current_round_index)
    nav_history = team.nav_history
    last_return = None
    if len(nav_history) >= 2:
        last_return = (nav_history[-1] / nav_history[-2]) - 1

    return render_template(
        "play.html",
        team=team,
        nav_history=nav_history,
        last_return=last_return,
        current_round=current_round,
        current_round_index=current_round_index,
        total_rounds=GAME_STATE.num_rounds,
        submitted=submitted,
        finished=finished,
        assets=ASSETS,
        asset_names=ASSET_FRIENDLY_NAMES,
    )


@app.route("/admin", methods=["GET", "POST"])
def admin():
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
        if action == "advance":
            if GAME_STATE.advance_round():
                if GAME_STATE.is_finished:
                    flash("Final round completed. Game over!", "success")
                else:
                    flash(f"Moved to round {GAME_STATE.current_round}.", "success")
            else:
                flash("Cannot advance; the game is already finished.", "info")
        elif action == "reset":
            GAME_STATE.reset()
            flash("Game has been reset.", "success")
        return redirect(url_for("admin"))

    current_round_index = GAME_STATE.current_round
    submissions = 0
    if not GAME_STATE.is_finished:
        for team in GAME_STATE.teams.values():
            if team.has_allocation(current_round_index):
                submissions += 1

    return render_template(
        "admin.html",
        authorized=True,
        game_state=GAME_STATE,
        submissions=submissions,
    )


@app.route("/leaderboard")
def leaderboard():
    teams_sorted = sorted(GAME_STATE.teams.values(), key=lambda t: t.current_nav, reverse=True)
    winner = teams_sorted[0] if GAME_STATE.is_finished and teams_sorted else None
    return render_template(
        "leaderboard.html",
        teams=teams_sorted,
        game_state=GAME_STATE,
        winner=winner,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
