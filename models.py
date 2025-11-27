"""Core models for the Open Outcry trading game."""
from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from game_config import (
    IMPACT_FACTOR,
    IMPACT_SIZE,
    INSTRUMENTS,
    NEWS_EVENTS,
    SESSION_DURATION_SECONDS,
    STARTING_CASH,
    TICK_SECONDS,
)


@dataclass
class Instrument:
    code: str
    name: str
    base_price: float
    last_price: float = field(init=False)

    def __post_init__(self):
        self.last_price = self.base_price


@dataclass
class Order:
    id: str
    team: str
    instrument: str
    side: str  # buy or sell
    qty: float
    limit_price: Optional[float]
    remaining: float
    timestamp: float

    @property
    def is_buy(self) -> bool:
        return self.side.lower() == "buy"


@dataclass
class Trade:
    id: str
    instrument: str
    price: float
    qty: float
    buy_team: str
    sell_team: str
    timestamp: float


@dataclass
class Team:
    name: str
    cash: float = STARTING_CASH
    positions: Dict[str, float] = field(default_factory=dict)
    nav_history: List[float] = field(default_factory=list)
    fills: List[Trade] = field(default_factory=list)

    @property
    def current_nav(self) -> float:
        return self.nav_history[-1] if self.nav_history else STARTING_CASH

    def record_nav(self, nav: float) -> None:
        self.nav_history.append(nav)


class GameState:
    def __init__(self, start_time: Optional[float] = None):
        self.instruments: Dict[str, Instrument] = {
            inst["code"]: Instrument(inst["code"], inst["name"], inst["base_price"]) for inst in INSTRUMENTS
        }
        self.teams: Dict[str, Team] = {}
        self.orderbooks: Dict[str, Dict[str, List[Order]]] = {
            code: {"bids": [], "asks": []} for code in self.instruments
        }
        self.trades: List[Trade] = []
        self.news_feed: List[Dict[str, str]] = []
        self.news_cursor = 0
        self.start_time = start_time or time.time()
        self.last_tick = self.start_time
        self.active = True
        self.duration = SESSION_DURATION_SECONDS
        self.tick_seconds = TICK_SECONDS
        self.price_history: Dict[str, List[Dict[str, float]]] = {
            code: [{"t": 0, "p": inst.base_price}] for code, inst in self.instruments.items()
        }

    @property
    def elapsed(self) -> float:
        return max(0.0, time.time() - self.start_time)

    @property
    def remaining(self) -> float:
        return max(0.0, self.duration - self.elapsed)

    def reset(self):
        self.__init__()

    def register_team(self, name: str):
        if not name:
            raise ValueError("Team name is required.")
        if name in self.teams:
            raise ValueError("Team name already taken.")
        team = Team(name=name)
        team.record_nav(STARTING_CASH)
        self.teams[name] = team

    def place_order(self, team_name: str, instrument: str, side: str, qty: float, limit_price: Optional[float]):
        if team_name not in self.teams:
            raise ValueError("Unknown team.")
        if instrument not in self.instruments:
            raise ValueError("Unknown instrument.")
        if qty <= 0:
            raise ValueError("Quantity must be positive.")
        side = side.lower()
        if side not in {"buy", "sell"}:
            raise ValueError("Side must be buy or sell.")

        order = Order(
            id=str(uuid.uuid4())[:8],
            team=team_name,
            instrument=instrument,
            side=side,
            qty=qty,
            remaining=qty,
            limit_price=limit_price,
            timestamp=time.time(),
        )
        book = self.orderbooks[instrument]
        self._match(order, book)
        if order.remaining > 0:
            book_key = "bids" if order.is_buy else "asks"
            book[book_key].append(order)
            self._sort_book(instrument)
        self.mark_to_market()

    def _sort_book(self, instrument: str):
        book = self.orderbooks[instrument]
        book["bids"].sort(key=lambda o: (-o.limit_price if o.limit_price is not None else float("inf"), o.timestamp))
        book["asks"].sort(key=lambda o: (o.limit_price if o.limit_price is not None else 0.0, o.timestamp))

    def _match(self, incoming: Order, book: Dict[str, List[Order]]):
        opposite_key = "asks" if incoming.is_buy else "bids"
        same_key = "bids" if incoming.is_buy else "asks"
        opposite = book[opposite_key]

        def price_crosses(a: Order, b: Order) -> bool:
            if a.limit_price is None or b.limit_price is None:
                return True
            if a.is_buy:
                return a.limit_price >= b.limit_price
            return b.limit_price >= a.limit_price

        while incoming.remaining > 0 and opposite:
            best = opposite[0]
            if not price_crosses(incoming, best):
                break
            trade_qty = min(incoming.remaining, best.remaining)
            trade_price = best.limit_price if best.limit_price is not None else incoming.limit_price or self.instruments[incoming.instrument].last_price
            self._execute_trade(incoming, best, trade_qty, trade_price)
            if best.remaining <= 0:
                opposite.pop(0)
        # Resort after possible modifications
        book[opposite_key] = opposite
        self._sort_book(incoming.instrument)
        # If incoming was market and still remains, convert to resting with last price
        if incoming.remaining > 0 and incoming.limit_price is None:
            incoming.limit_price = self.instruments[incoming.instrument].last_price

    def _execute_trade(self, incoming: Order, resting: Order, qty: float, price: float):
        incoming.remaining -= qty
        resting.remaining -= qty

        if incoming.is_buy:
            buy_team = self.teams[incoming.team]
            sell_team = self.teams[resting.team]
        else:
            buy_team = self.teams[resting.team]
            sell_team = self.teams[incoming.team]

        buy_team.cash -= price * qty
        sell_team.cash += price * qty
        buy_team.positions[incoming.instrument] = buy_team.positions.get(incoming.instrument, 0.0) + qty
        sell_team.positions[incoming.instrument] = sell_team.positions.get(incoming.instrument, 0.0) - qty

        trade = Trade(
            id=str(uuid.uuid4())[:8],
            instrument=incoming.instrument,
            price=price,
            qty=qty,
            buy_team=buy_team.name,
            sell_team=sell_team.name,
            timestamp=time.time(),
        )
        self.trades.append(trade)
        buy_team.fills.append(trade)
        sell_team.fills.append(trade)

        # price impact
        impact = (qty / IMPACT_SIZE) * IMPACT_FACTOR
        direction = 1 if incoming.is_buy else -1
        self._nudge_price(incoming.instrument, direction * impact)

    def _nudge_price(self, instrument: str, pct_move: float):
        inst = self.instruments[instrument]
        inst.last_price = max(0.01, inst.last_price * (1 + pct_move))

    def tick(self):
        now = time.time()
        while self.last_tick + self.tick_seconds <= now and self.active:
            self.last_tick += self.tick_seconds
            t_elapsed = self.last_tick - self.start_time
            self._process_news(t_elapsed)
            for inst in self.instruments.values():
                # mean reversion to base price with noise
                anchor = inst.base_price
                distance = (inst.last_price - anchor) / anchor
                revert = -0.05 * distance
                noise = 0.01 * math.sin(t_elapsed / 15.0 + hash(inst.code) % 7) + 0.003 * math.cos(t_elapsed / 9.0)
                shock_bias = 0.0
                for n in self.news_feed[-3:]:
                    shock_bias += n.get("shock", {}).get(inst.code, 0.0) * 0.001
                change = revert + noise + shock_bias
                inst.last_price = max(0.01, inst.last_price * (1 + change))
                self.price_history[inst.code].append({"t": t_elapsed, "p": inst.last_price})
            self.mark_to_market()
            if self.remaining <= 0:
                self.active = False
                break

    def _process_news(self, elapsed_seconds: float):
        while self.news_cursor < len(NEWS_EVENTS) and elapsed_seconds >= NEWS_EVENTS[self.news_cursor]["second"]:
            event = NEWS_EVENTS[self.news_cursor]
            payload = {"t": elapsed_seconds, "headline": event["headline"], "shock": event.get("shock", {})}
            self.news_feed.append(payload)
            self.news_cursor += 1

    def mark_to_market(self):
        prices = {code: inst.last_price for code, inst in self.instruments.items()}
        for team in self.teams.values():
            nav = team.cash
            for code, qty in team.positions.items():
                nav += qty * prices.get(code, 0.0)
            team.record_nav(nav)

    def state_for_team(self, team_name: Optional[str], include_private: bool = False) -> Dict:
        self.tick()
        team = self.teams.get(team_name) if team_name else None
        data = {
            "active": self.active,
            "elapsed": self.elapsed,
            "remaining": self.remaining,
            "instruments": {
                code: {
                    "name": inst.name,
                    "last_price": inst.last_price,
                    "bid": self.orderbooks[code]["bids"][0].limit_price if self.orderbooks[code]["bids"] else None,
                    "ask": self.orderbooks[code]["asks"][0].limit_price if self.orderbooks[code]["asks"] else None,
                    "history": self.price_history[code][-200:],
                }
                for code, inst in self.instruments.items()
            },
            "news": self.news_feed[-20:],
            "recent_trades": [
                {
                    "instrument": t.instrument,
                    "price": t.price,
                    "qty": t.qty,
                    "timestamp": t.timestamp,
                }
                for t in self.trades[-40:]
            ],
        }
        if team:
            data["team"] = {
                "name": team.name,
                "cash": team.cash,
                "positions": team.positions,
                "nav_history": team.nav_history[-200:],
                "fills": [
                    {"instrument": t.instrument, "price": t.price, "qty": t.qty, "timestamp": t.timestamp}
                    for t in team.fills[-20:]
                ],
            }
        if include_private:
            data["leaderboard"] = sorted(
                (
                    {
                        "team": t.name,
                        "nav": t.current_nav,
                        "cash": t.cash,
                    }
                    for t in self.teams.values()
                ),
                key=lambda x: x["nav"],
                reverse=True,
            )
            data["orderbooks"] = {
                code: {
                    "bids": [self._serialize_order(o) for o in book["bids"]],
                    "asks": [self._serialize_order(o) for o in book["asks"]],
                }
                for code, book in self.orderbooks.items()
            }
        return data

    @staticmethod
    def _serialize_order(order: Order) -> Dict:
        return {
            "id": order.id,
            "team": order.team,
            "side": order.side,
            "qty": order.qty,
            "remaining": order.remaining,
            "limit_price": order.limit_price,
            "timestamp": order.timestamp,
        }

