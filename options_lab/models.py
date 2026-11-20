from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"


@dataclass(frozen=True)
class OptionContract:
    strike: float
    expiry_years: float
    option_type: OptionType = OptionType.CALL

    def __post_init__(self) -> None:
        if self.strike <= 0:
            raise ValueError("strike must be positive")
        if self.expiry_years <= 0:
            raise ValueError("expiry_years must be positive")

    def payoff(self, spot: float) -> float:
        if spot < 0:
            raise ValueError("spot cannot be negative")
        if self.option_type is OptionType.CALL:
            return max(spot - self.strike, 0.0)
        return max(self.strike - spot, 0.0)


@dataclass(frozen=True)
class MarketState:
    spot: float
    rate: float
    volatility: float
    timestamp_years: float = 0.0

    def __post_init__(self) -> None:
        if self.spot <= 0:
            raise ValueError("spot must be positive")
        if self.volatility < 0:
            raise ValueError("volatility cannot be negative")
        if self.timestamp_years < 0:
            raise ValueError("timestamp_years cannot be negative")


@dataclass(frozen=True)
class Quote:
    theoretical_value: float
    bid: float
    ask: float
    inventory_adjustment: float = 0.0

    def __post_init__(self) -> None:
        if self.theoretical_value < 0 or self.bid < 0:
            raise ValueError("quote values cannot be negative")
        if self.ask < self.bid:
            raise ValueError("ask must be at least bid")


@dataclass(frozen=True)
class HedgeTrade:
    timestamp_years: float
    delta_before: float
    hedge_quantity: float
    underlying_price: float
    execution_cost: float


@dataclass(frozen=True)
class PnLAttribution:
    spread_capture: float = 0.0
    hedge_pnl: float = 0.0
    inventory_pnl: float = 0.0
    fees: float = 0.0
    model_error: float = 0.0

    @property
    def total(self) -> float:
        return self.spread_capture + self.hedge_pnl + self.inventory_pnl + self.model_error - self.fees


@dataclass(frozen=True)
class MarketMakerPolicy:
    half_spread: float = 0.10
    inventory_skew: float = 0.03
    inventory_limit: int = 10
    hedge_threshold: float = 0.10
    transaction_cost_rate: float = 0.0001

    def __post_init__(self) -> None:
        if self.half_spread < 0 or self.inventory_skew < 0:
            raise ValueError("spread and skew must be nonnegative")
        if self.inventory_limit <= 0:
            raise ValueError("inventory_limit must be positive")
        if self.hedge_threshold < 0 or self.transaction_cost_rate < 0:
            raise ValueError("hedge threshold and cost rate must be nonnegative")
