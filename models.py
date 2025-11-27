from __future__ import annotations

import math
import random
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List

from game_config import ASSET_BASELINES, ASSETS, ASSET_FRIENDLY_NAMES, EVENTS


@dataclass
class Team:
    name: str
    nav_history: List[float]
    allocation: Dict[str, float]

    @property
    def current_nav(self) -> float:
        return self.nav_history[-1]


class GameState:
    def __init__(self, starting_nav: float = 100.0, total_duration_seconds: int = 40 * 60, tick_seconds: int = 3):
        self.starting_nav = starting_nav
        self.total_duration_seconds = total_duration_seconds
        self.tick_seconds = tick_seconds
        self.assets = ASSETS
        self.teams: Dict[str, Team] = {}
        self.asset_index_histories: Dict[str, List[float]] = {asset: [100.0] for asset in self.assets}
        self.market_index_history: List[float] = [100.0]
        self.flow_skew: Dict[str, float] = {asset: 0.0 for asset in self.assets}
        self.trade_requests: List[Dict[str, str]] = []
        self.news_feed: List[Dict[str, str]] = []
        self.game_start_ts = time.time()
        self.last_tick_ts = self.game_start_ts
        self.sim_day = 0
        self.events = sorted(EVENTS, key=lambda e: e["time_offset"])
        self._timestamp_message("Session armed — continuous tape live for 40 minutes. No rounds, pure flow.")

    @property
    def is_finished(self) -> bool:
        return self.total_seconds_left <= 0

    @property
    def total_seconds_left(self) -> int:
        elapsed = int(time.time() - self.game_start_ts)
        remaining = self.total_duration_seconds - elapsed
        return max(0, remaining)

    def _timestamp_message(self, message: str) -> None:
        ts = time.strftime("%H:%M:%S", time.localtime())
        self.news_feed.append({"time": ts, "message": message})
        if len(self.news_feed) > 120:
            self.news_feed = self.news_feed[-120:]

    def register_team(self, name: str) -> None:
        normalized = name.strip()
        if not normalized:
            raise ValueError("Team name cannot be empty.")
        for existing in self.teams:
            if existing.lower() == normalized.lower():
                raise ValueError("That team name is already taken.")
        default_alloc = {asset: (1.0 if asset == "CASH" else 0.0) for asset in self.assets}
        self.teams[normalized] = Team(name=normalized, nav_history=[self.starting_nav], allocation=default_alloc)
        self._timestamp_message(f"Team {normalized} connected to the tape.")

    def update_allocation(self, team_name: str, weights: Dict[str, float]) -> None:
        if team_name not in self.teams:
            raise ValueError("Team not registered.")
        clean = {asset: max(0.0, weights.get(asset, 0.0)) for asset in self.assets}
        total = sum(clean.values())
        if total <= 0:
            raise ValueError("Provide at least one positive weight.")
        normalized = {asset: val / total for asset, val in clean.items()}
        self.teams[team_name].allocation = normalized
        self._timestamp_message(f"{team_name} refreshed allocation; flows updating.")

    def add_trade_request(self, team_name: str, asset: str, side: str, price: str, note: str = "") -> str:
        if asset not in self.assets:
            raise ValueError("Unknown asset")
        if side.lower() not in {"long", "short"}:
            raise ValueError("Side must be long or short")
        trade_id = uuid.uuid4().hex[:8]
        payload = {
            "id": trade_id,
            "team": team_name,
            "asset": asset,
            "side": side.lower(),
            "price": price,
            "note": note,
            "status": "pending",
            "ts": time.strftime("%H:%M:%S", time.localtime()),
        }
        self.trade_requests.append(payload)
        self._timestamp_message(f"{team_name} yells {side.upper()} {asset} @ {price} — host to confirm.")
        return trade_id

    def accept_trade(self, trade_id: str) -> None:
        for trade in self.trade_requests:
            if trade["id"] == trade_id and trade.get("status") == "pending":
                trade["status"] = "accepted"
                magnitude = 0.015
                if trade["side"] == "short":
                    magnitude *= -1
                self.flow_skew[trade["asset"]] = max(min(self.flow_skew.get(trade["asset"], 0.0) + magnitude, 0.12), -0.12)
                self._timestamp_message(f"HOST FILLED {trade['side'].upper()} {trade['asset']} @ {trade['price']} for {trade['team']}")
                return
        raise ValueError("Trade not found or already processed")

    def reject_trade(self, trade_id: str) -> None:
        for trade in self.trade_requests:
            if trade["id"] == trade_id and trade.get("status") == "pending":
                trade["status"] = "rejected"
                self._timestamp_message(f"HOST REJECTED {trade['side'].upper()} {trade['asset']} for {trade['team']}")
                return
        raise ValueError("Trade not found or already processed")

    def _flow_adjustments(self) -> Dict[str, float]:
        if not self.teams:
            return {asset: 0.0 for asset in self.assets}
        baseline = 1.0 / len(self.assets)
        total_weights = {asset: 0.0 for asset in self.assets}
        for team in self.teams.values():
            for asset in self.assets:
                total_weights[asset] += team.allocation.get(asset, 0.0)
        avg_weights = {asset: total_weights[asset] / len(self.teams) for asset in self.assets}
        adj = {}
        for asset, weight in avg_weights.items():
            skew = weight - baseline
            trade_skew = self.flow_skew.get(asset, 0.0)
            adj[asset] = max(min(skew * 0.4 + trade_skew, 0.08), -0.08)
        return adj

    def _event_impact(self, now: float) -> Dict[str, float]:
        elapsed = now - self.game_start_ts
        impact = {asset: 0.0 for asset in self.assets}
        for event in self.events:
            if elapsed >= event["time_offset"]:
                decay = math.exp(-(elapsed - event["time_offset"]) / 240)
                for asset, shock in event["impact"].items():
                    impact[asset] += shock * decay
        return impact

    def _simulate_step(self) -> None:
        self.sim_day += 1
        now = time.time()
        event_impacts = self._event_impact(now)
        flow_adj = self._flow_adjustments()

        avg_allocation = {asset: 0.0 for asset in self.assets}
        if self.teams:
            for team in self.teams.values():
                for asset in self.assets:
                    avg_allocation[asset] += team.allocation.get(asset, 0.0)
            avg_allocation = {asset: val / len(self.teams) for asset, val in avg_allocation.items()}
        else:
            avg_allocation = {asset: 1.0 / len(self.assets) for asset in self.assets}

        market_return = 0.0
        asset_returns: Dict[str, float] = {}
        for asset in self.assets:
            base = ASSET_BASELINES[asset]
            shock = random.gauss(base["drift"], base["vol"])
            total_return = shock + event_impacts.get(asset, 0.0) + flow_adj.get(asset, 0.0)
            asset_returns[asset] = total_return
            market_return += avg_allocation.get(asset, 0.0) * total_return
            next_level = self.asset_index_histories[asset][-1] * (1 + total_return)
            self.asset_index_histories[asset].append(max(next_level, 0.01))

        self.market_index_history.append(max(self.market_index_history[-1] * (1 + market_return), 0.01))

        for team in self.teams.values():
            portfolio_return = sum(team.allocation.get(asset, 0.0) * asset_returns[asset] for asset in self.assets)
            new_nav = team.current_nav * (1 + portfolio_return)
            team.nav_history.append(max(new_nav, 0.01))

        # decay flow skew so bursts fade quickly
        self.flow_skew = {asset: value * 0.55 for asset, value in self.flow_skew.items()}

    def sync_to_time(self) -> None:
        if self.is_finished:
            return
        now = time.time()
        steps = int((now - self.last_tick_ts) // self.tick_seconds)
        if steps <= 0:
            return
        for _ in range(steps):
            self._simulate_step()
        self.last_tick_ts += steps * self.tick_seconds

    def reset(self) -> None:
        self.teams.clear()
        self.asset_index_histories = {asset: [100.0] for asset in self.assets}
        self.market_index_history = [100.0]
        self.flow_skew = {asset: 0.0 for asset in self.assets}
        self.trade_requests.clear()
        self.news_feed.clear()
        self.game_start_ts = time.time()
        self.last_tick_ts = self.game_start_ts
        self.sim_day = 0
        self._timestamp_message("Simulation reset — tape restarted.")
