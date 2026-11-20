from __future__ import annotations

import math
import random
from dataclasses import dataclass
from statistics import fmean, stdev

from .models import MarketState, OptionContract


@dataclass(frozen=True)
class MonteCarloEstimate:
    price: float
    standard_error: float
    ci_low: float
    ci_high: float
    paths: int
    seed: int


def monte_carlo_price(
    contract: OptionContract,
    state: MarketState,
    *,
    paths: int = 20_000,
    seed: int = 7,
    confidence_z: float = 1.96,
) -> MonteCarloEstimate:
    if paths < 2:
        raise ValueError("paths must be at least 2")

    rng = random.Random(seed)
    time = contract.expiry_years
    drift = (state.rate - 0.5 * state.volatility * state.volatility) * time
    diffusion = state.volatility * math.sqrt(time)
    discount = math.exp(-state.rate * time)
    discounted_payoffs: list[float] = []

    for _ in range(paths):
        terminal_spot = state.spot * math.exp(drift + diffusion * rng.gauss(0.0, 1.0))
        discounted_payoffs.append(discount * contract.payoff(terminal_spot))

    price = fmean(discounted_payoffs)
    standard_error = stdev(discounted_payoffs) / math.sqrt(paths)
    return MonteCarloEstimate(
        price=price,
        standard_error=standard_error,
        ci_low=price - confidence_z * standard_error,
        ci_high=price + confidence_z * standard_error,
        paths=paths,
        seed=seed,
    )
