from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .models import HedgeTrade, MarketState, OptionContract, PnLAttribution
from .pricing import black_scholes_greeks, black_scholes_price


@dataclass(frozen=True)
class HedgeSimulationResult:
    terminal_spot: float
    option_payoff: float
    final_equity: float
    attribution: PnLAttribution
    trades: tuple[HedgeTrade, ...]
    path: tuple[float, ...]


def geometric_brownian_path(
    state: MarketState,
    *,
    horizon_years: float,
    steps: int,
    actual_volatility: float | None = None,
    seed: int = 7,
) -> tuple[float, ...]:
    if horizon_years <= 0 or steps <= 0:
        raise ValueError("horizon and steps must be positive")
    volatility = state.volatility if actual_volatility is None else actual_volatility
    if volatility < 0:
        raise ValueError("actual_volatility cannot be negative")

    rng = random.Random(seed)
    dt = horizon_years / steps
    drift = (state.rate - 0.5 * volatility * volatility) * dt
    diffusion = volatility * math.sqrt(dt)
    spots = [state.spot]
    for _ in range(steps):
        spots.append(spots[-1] * math.exp(drift + diffusion * rng.gauss(0.0, 1.0)))
    return tuple(spots)


def simulate_delta_hedge(
    contract: OptionContract,
    state: MarketState,
    *,
    steps: int = 52,
    actual_volatility: float | None = None,
    pricing_volatility: float | None = None,
    transaction_cost_rate: float = 0.0,
    seed: int = 7,
) -> HedgeSimulationResult:
    if transaction_cost_rate < 0:
        raise ValueError("transaction_cost_rate cannot be negative")
    pricing_vol = state.volatility if pricing_volatility is None else pricing_volatility
    if pricing_vol < 0:
        raise ValueError("pricing_volatility cannot be negative")

    path = geometric_brownian_path(
        state,
        horizon_years=contract.expiry_years,
        steps=steps,
        actual_volatility=actual_volatility,
        seed=seed,
    )
    dt = contract.expiry_years / steps
    pricing_state = MarketState(path[0], state.rate, pricing_vol)
    premium = black_scholes_price(contract, pricing_state)
    shares = black_scholes_greeks(contract, pricing_state)["delta"]
    first_cost = abs(shares * path[0]) * transaction_cost_rate
    cash = premium - shares * path[0] - first_cost
    fees = first_cost
    trades = [HedgeTrade(0.0, 0.0, shares, path[0], first_cost)]

    for step in range(1, steps + 1):
        cash *= math.exp(state.rate * dt)
        if step == steps:
            break
        remaining = contract.expiry_years - step * dt
        rolling_contract = OptionContract(contract.strike, remaining, contract.option_type)
        rolling_state = MarketState(path[step], state.rate, pricing_vol, step * dt)
        target_shares = black_scholes_greeks(rolling_contract, rolling_state)["delta"]
        quantity = target_shares - shares
        cost = abs(quantity * path[step]) * transaction_cost_rate
        cash -= quantity * path[step] + cost
        fees += cost
        trades.append(HedgeTrade(step * dt, shares, quantity, path[step], cost))
        shares = target_shares

    payoff = contract.payoff(path[-1])
    final_equity = cash + shares * path[-1] - payoff
    attribution = PnLAttribution(hedge_pnl=final_equity + fees, fees=fees)
    return HedgeSimulationResult(
        terminal_spot=path[-1],
        option_payoff=payoff,
        final_equity=final_equity,
        attribution=attribution,
        trades=tuple(trades),
        path=path,
    )
