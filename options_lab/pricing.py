from __future__ import annotations

import math

from .models import MarketState, OptionContract, OptionType


def normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def normal_pdf(value: float) -> float:
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


def _d1_d2(contract: OptionContract, state: MarketState) -> tuple[float, float]:
    time = contract.expiry_years
    sigma_sqrt_t = state.volatility * math.sqrt(time)
    if sigma_sqrt_t <= 0:
        raise ValueError("d1 and d2 are undefined at zero volatility")
    d1 = (
        math.log(state.spot / contract.strike)
        + (state.rate + 0.5 * state.volatility * state.volatility) * time
    ) / sigma_sqrt_t
    return d1, d1 - sigma_sqrt_t


def black_scholes_price(contract: OptionContract, state: MarketState) -> float:
    discount = math.exp(-state.rate * contract.expiry_years)
    if state.volatility == 0:
        forward_intrinsic = state.spot - contract.strike * discount
        return max(forward_intrinsic, 0.0) if contract.option_type is OptionType.CALL else max(-forward_intrinsic, 0.0)

    d1, d2 = _d1_d2(contract, state)
    if contract.option_type is OptionType.CALL:
        value = state.spot * normal_cdf(d1) - contract.strike * discount * normal_cdf(d2)
    else:
        value = contract.strike * discount * normal_cdf(-d2) - state.spot * normal_cdf(-d1)
    return max(value, 0.0)


def black_scholes_greeks(contract: OptionContract, state: MarketState) -> dict[str, float]:
    if state.volatility == 0:
        discount = math.exp(-state.rate * contract.expiry_years)
        forward_intrinsic = state.spot - contract.strike * discount
        if contract.option_type is OptionType.CALL:
            delta = 1.0 if forward_intrinsic > 0 else 0.0
        else:
            delta = -1.0 if forward_intrinsic < 0 else 0.0
        return {"delta": delta, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}

    d1, d2 = _d1_d2(contract, state)
    time = contract.expiry_years
    discount = math.exp(-state.rate * time)
    pdf = normal_pdf(d1)
    gamma = pdf / (state.spot * state.volatility * math.sqrt(time))
    vega = state.spot * pdf * math.sqrt(time)
    common_theta = -(state.spot * pdf * state.volatility) / (2.0 * math.sqrt(time))

    if contract.option_type is OptionType.CALL:
        delta = normal_cdf(d1)
        theta = common_theta - state.rate * contract.strike * discount * normal_cdf(d2)
        rho = contract.strike * time * discount * normal_cdf(d2)
    else:
        delta = normal_cdf(d1) - 1.0
        theta = common_theta + state.rate * contract.strike * discount * normal_cdf(-d2)
        rho = -contract.strike * time * discount * normal_cdf(-d2)

    return {"delta": delta, "gamma": gamma, "vega": vega, "theta": theta, "rho": rho}


def binomial_price(contract: OptionContract, state: MarketState, steps: int = 200) -> float:
    if steps <= 0:
        raise ValueError("steps must be positive")
    if state.volatility == 0:
        return black_scholes_price(contract, state)

    dt = contract.expiry_years / steps
    up = math.exp(state.volatility * math.sqrt(dt))
    down = 1.0 / up
    growth = math.exp(state.rate * dt)
    probability = (growth - down) / (up - down)
    if not 0.0 <= probability <= 1.0:
        raise ValueError("binomial parameters imply an invalid risk-neutral probability")
    discount = math.exp(-state.rate * dt)

    values = [
        contract.payoff(state.spot * (up ** j) * (down ** (steps - j)))
        for j in range(steps + 1)
    ]
    for level in range(steps, 0, -1):
        values = [
            discount * (probability * values[j + 1] + (1.0 - probability) * values[j])
            for j in range(level)
        ]
    return values[0]
