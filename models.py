from __future__ import annotations

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
    def __init__(self, assets: List[str], rounds: List[Round], starting_nav: float = 100.0):
        self.assets = assets
        self.rounds = rounds
        self.num_rounds = len(rounds)
        self.starting_nav = starting_nav
        self.current_round = 1
        self.teams: Dict[str, Team] = {}

    @property
    def is_finished(self) -> bool:
        return self.current_round > self.num_rounds

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

    def advance_round(self) -> bool:
        if self.is_finished:
            return False

        current_round_obj = self.rounds[self.current_round - 1]
        for team in self.teams.values():
            allocation = self._get_allocation_for_round(team, self.current_round)
            portfolio_return = sum(
                allocation.get(asset, 0.0) * current_round_obj.returns.get(asset, 0.0)
                for asset in self.assets
            )
            new_nav = team.current_nav * (1 + portfolio_return)
            team.nav_history.append(new_nav)

        self.current_round += 1
        return True

    def reset(self) -> None:
        self.current_round = 1
        for team in self.teams.values():
            team.nav_history = [self.starting_nav]
            team.allocations.clear()
        self.teams.clear()
