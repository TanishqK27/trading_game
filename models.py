from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Round:
    index: int
    name: str
    news: str
    returns: Dict[str, float]


class Team:
    def __init__(self, name: str, starting_nav: float = 100.0):
        self.name = name
        self.nav_history: List[float] = [starting_nav]
        self.allocations: Dict[int, Dict[str, float]] = {}

    @property
    def current_nav(self) -> float:
        return self.nav_history[-1]

    def last_return(self) -> Optional[float]:
        if len(self.nav_history) < 2:
            return None
        prev = self.nav_history[-2]
        if prev == 0:
            return None
        return (self.current_nav / prev) - 1

    def has_allocation(self, round_index: int) -> bool:
        return round_index in self.allocations


class GameState:
    def __init__(
        self,
        assets: List[str],
        rounds: List[Round],
        starting_nav: float = 100.0,
        total_duration_seconds: int = 40 * 60,
    ):
        self.assets = assets
        self.rounds = rounds
        self.num_rounds = len(rounds)
        self.starting_nav = starting_nav
        self.current_round = 1
        self.teams: Dict[str, Team] = {}
        self.total_duration_seconds = total_duration_seconds
        # Spread scenario beats evenly across the session to feel continuous.
        self.round_duration_seconds = max(60, int(total_duration_seconds / max(1, self.num_rounds)))
        now = time.time()
        self.game_start_ts = now
        self.round_start_ts = now
        self.market_index_history: List[float] = [100.0]
        self.asset_index_histories: Dict[str, List[float]] = {
            asset: [100.0] for asset in self.assets
        }
        self.news_feed: List[Dict[str, str]] = []
        self.trade_requests: List[Dict[str, str]] = []
        self.flow_skew: Dict[str, float] = {asset: 0.0 for asset in self.assets}
        self._timestamp_message("Session armed – waiting for allocations before Round 1 closes.")

    @property
    def is_finished(self) -> bool:
        return self.current_round > self.num_rounds

    @property
    def seconds_left_in_round(self) -> int:
        self.sync_to_time()
        if self.is_finished:
            return 0
        elapsed = int(time.time() - self.round_start_ts)
        remaining = self.round_duration_seconds - elapsed
        return max(0, remaining)

    @property
    def total_seconds_left(self) -> int:
        if self.is_finished:
            return 0
        elapsed_total = int(time.time() - self.game_start_ts)
        remaining = self.total_duration_seconds - elapsed_total
        return max(0, remaining)

    def _timestamp_message(self, message: str) -> None:
        ts = time.strftime("%H:%M:%S", time.localtime())
        self.news_feed.append({"time": ts, "message": message})
        if len(self.news_feed) > 80:
            self.news_feed = self.news_feed[-80:]

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
        self._timestamp_message(
            f"{team_name} yells {side.upper()} {asset} @ {price} — host to confirm."
        )
        return trade_id

    def accept_trade(self, trade_id: str) -> None:
        for trade in self.trade_requests:
            if trade["id"] == trade_id and trade.get("status") == "pending":
                trade["status"] = "accepted"
                magnitude = 0.02  # modest market impact bump
                if trade["side"] == "short":
                    magnitude *= -1
                self.flow_skew[trade["asset"]] = max(
                    min(self.flow_skew.get(trade["asset"], 0.0) + magnitude, 0.08),
                    -0.08,
                )
                self._timestamp_message(
                    f"HOST FILLED {trade['side'].upper()} {trade['asset']} @ {trade['price']} for {trade['team']}"
                )
                return
        raise ValueError("Trade not found or already processed")

    def reject_trade(self, trade_id: str) -> None:
        for trade in self.trade_requests:
            if trade["id"] == trade_id and trade.get("status") == "pending":
                trade["status"] = "rejected"
                self._timestamp_message(
                    f"HOST REJECTED {trade['side'].upper()} {trade['asset']} for {trade['team']}"
                )
                return
        raise ValueError("Trade not found or already processed")

    def register_team(self, name: str) -> None:
        if not name:
            raise ValueError("Team name cannot be empty.")
        normalized = name.strip()
        for existing in self.teams:
            if existing.lower() == normalized.lower():
                raise ValueError("That team name is already taken.")
        self.teams[normalized] = Team(normalized, starting_nav=self.starting_nav)

    def record_allocation(self, team_name: str, round_index: int, weights: Dict[str, float]) -> None:
        if team_name not in self.teams:
            raise ValueError("Team not registered.")
        if self.is_finished:
            raise ValueError("The game has already finished.")
        if round_index != self.current_round:
            raise ValueError("Allocations can only be submitted for the current round.")
        team = self.teams[team_name]
        if team.has_allocation(round_index):
            raise ValueError("Allocation already submitted for this round.")

        # Ensure all assets exist; missing ones are zero-weight
        clean_weights = {asset: weights.get(asset, 0.0) for asset in self.assets}
        # Normalize to ensure sum is 1.0
        total = sum(clean_weights.values())
        if total <= 0:
            raise ValueError("Allocation must include at least one asset.")
        normalized = {asset: weight / total for asset, weight in clean_weights.items()}
        team.allocations[round_index] = normalized

    def _find_latest_allocation(self, team: Team) -> Dict[str, float]:
        if not team.allocations:
            fallback = {asset: 0.0 for asset in self.assets}
            if "CASH" in fallback:
                fallback["CASH"] = 1.0
            return fallback
        latest_round = max(team.allocations.keys())
        return team.allocations[latest_round]

    def _get_allocation_for_round(self, team: Team, round_index: int) -> Dict[str, float]:
        if round_index in team.allocations:
            return team.allocations[round_index]
        # Carry forward the most recent allocation if available
        previous_rounds = [idx for idx in team.allocations if idx < round_index]
        if previous_rounds:
            latest_round = max(previous_rounds)
            return team.allocations[latest_round]
        return {asset: 1.0 if asset == "CASH" else 0.0 for asset in self.assets}

    def _compute_flow_adjustment(self) -> Dict[str, float]:
        if not self.teams:
            return {asset: 0.0 for asset in self.assets}

        baseline = 1.0 / len(self.assets)
        total_weights = {asset: 0.0 for asset in self.assets}
        for team in self.teams.values():
            allocation = self._get_allocation_for_round(team, self.current_round)
            for asset in self.assets:
                total_weights[asset] += allocation.get(asset, 0.0)

        avg_weights = {asset: total_weights[asset] / len(self.teams) for asset in self.assets}
        adjustment = {}
        for asset, weight in avg_weights.items():
            skew = weight - baseline
            trade_skew = self.flow_skew.get(asset, 0.0)
            adjustment[asset] = max(min((skew * 0.5) + trade_skew, 0.08), -0.08)
        return adjustment

    def sync_to_time(self) -> None:
        """Auto-advance scenario beats based on the 40-minute clock."""
        while (
            not self.is_finished
            and (time.time() - self.round_start_ts) >= self.round_duration_seconds
        ):
            progressed = self.advance_round(auto=True)
            if not progressed:
                break

    def advance_round(self, auto: bool = False) -> bool:
        if self.is_finished:
            return False

        current_round_obj = self.rounds[self.current_round - 1]
        flow_adjustment = self._compute_flow_adjustment()
        for team in self.teams.values():
            allocation = self._get_allocation_for_round(team, self.current_round)
            portfolio_return = sum(
                allocation.get(asset, 0.0)
                * (current_round_obj.returns.get(asset, 0.0) + flow_adjustment.get(asset, 0.0))
                for asset in self.assets
            )
            new_nav = team.current_nav * (1 + portfolio_return)
            team.nav_history.append(new_nav)

        avg_allocation = {asset: 0.0 for asset in self.assets}
        if self.teams:
            for team in self.teams.values():
                allocation = self._get_allocation_for_round(team, self.current_round)
                for asset in self.assets:
                    avg_allocation[asset] += allocation.get(asset, 0.0)
            avg_allocation = {
                asset: weight / len(self.teams) for asset, weight in avg_allocation.items()
            }
        else:
            avg_allocation = {asset: 1.0 / len(self.assets) for asset in self.assets}

        market_return = sum(
            avg_allocation.get(asset, 0.0)
            * (current_round_obj.returns.get(asset, 0.0) + flow_adjustment.get(asset, 0.0))
            for asset in self.assets
        )
        self.market_index_history.append(self.market_index_history[-1] * (1 + market_return))

        for asset in self.assets:
            asset_return = current_round_obj.returns.get(asset, 0.0) + flow_adjustment.get(asset, 0.0)
            next_val = self.asset_index_histories[asset][-1] * (1 + asset_return)
            self.asset_index_histories[asset].append(next_val)

        tag = "auto" if auto else "host"
        self._timestamp_message(
            f"[{tag}] Round {self.current_round} settled with flow-adjusted market move {market_return*100:.2f}%"
        )
        self.current_round += 1
        self.round_start_ts = time.time()
        # decay flow skew so bursts fade
        self.flow_skew = {asset: value * 0.4 for asset, value in self.flow_skew.items()}
        return True

    def reset(self) -> None:
        self.current_round = 1
        for team in self.teams.values():
            team.nav_history = [self.starting_nav]
            team.allocations.clear()
        self.teams.clear()
        self.market_index_history = [100.0]
        self.asset_index_histories = {asset: [100.0] for asset in self.assets}
        self.news_feed.clear()
        self.trade_requests.clear()
        self.flow_skew = {asset: 0.0 for asset in self.assets}
        now = time.time()
        self.game_start_ts = now
        self.round_start_ts = now
        self._timestamp_message("Game reset – Round 1 clock restarted.")
