from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass

from .hedging import geometric_brownian_path
from .models import HedgeTrade, MarketMakerPolicy, MarketState, OptionContract, PnLAttribution, Quote
from .pricing import black_scholes_greeks, black_scholes_price


@dataclass(frozen=True)
class MarketMakerResult:
    final_equity: float
    terminal_spot: float
    option_inventory: int
    stock_inventory: float
    accepted_orders: int
    rejected_orders: int
    attribution: PnLAttribution
    hedge_trades: tuple[HedgeTrade, ...]

    def to_dict(self) -> dict[str, object]:
        output = asdict(self)
        output["attribution"]["total"] = self.attribution.total
        return output


def make_quote(theoretical_value: float, inventory: int, policy: MarketMakerPolicy) -> Quote:
    inventory_adjustment = -inventory * policy.inventory_skew
    reservation_value = max(theoretical_value + inventory_adjustment, 0.0)
    bid = max(reservation_value - policy.half_spread, 0.0)
    ask = max(reservation_value + policy.half_spread, bid)
    return Quote(theoretical_value, bid, ask, inventory_adjustment)


def simulate_market_maker(
    contract: OptionContract,
    state: MarketState,
    policy: MarketMakerPolicy,
    *,
    steps: int = 52,
    order_probability: float = 0.45,
    customer_buy_probability: float = 0.5,
    actual_volatility: float | None = None,
    seed: int = 7,
) -> MarketMakerResult:
    if not 0.0 <= order_probability <= 1.0:
        raise ValueError("order_probability must be between 0 and 1")
    if not 0.0 <= customer_buy_probability <= 1.0:
        raise ValueError("customer_buy_probability must be between 0 and 1")

    path = geometric_brownian_path(
        state,
        horizon_years=contract.expiry_years,
        steps=steps,
        actual_volatility=actual_volatility,
        seed=seed,
    )
    rng = random.Random(seed + 1)
    dt = contract.expiry_years / steps
    cash = 0.0
    option_inventory = 0
    stock_inventory = 0.0
    spread_capture = 0.0
    fees = 0.0
    accepted = 0
    rejected = 0
    hedge_trades: list[HedgeTrade] = []

    for step in range(steps):
        if step > 0:
            cash *= math.exp(state.rate * dt)
        remaining = contract.expiry_years - step * dt
        rolling_contract = OptionContract(contract.strike, remaining, contract.option_type)
        rolling_state = MarketState(path[step], state.rate, state.volatility, step * dt)
        theoretical = black_scholes_price(rolling_contract, rolling_state)
        quote = make_quote(theoretical, option_inventory, policy)

        if rng.random() < order_probability:
            customer_buys = rng.random() < customer_buy_probability
            proposed_inventory = option_inventory - 1 if customer_buys else option_inventory + 1
            if abs(proposed_inventory) > policy.inventory_limit:
                rejected += 1
            else:
                option_inventory = proposed_inventory
                accepted += 1
                if customer_buys:
                    cash += quote.ask
                    spread_capture += quote.ask - theoretical
                else:
                    cash -= quote.bid
                    spread_capture += theoretical - quote.bid

        delta = black_scholes_greeks(rolling_contract, rolling_state)["delta"]
        target_stock = -option_inventory * delta
        quantity = target_stock - stock_inventory
        if abs(quantity) >= policy.hedge_threshold:
            cost = abs(quantity * path[step]) * policy.transaction_cost_rate
            cash -= quantity * path[step] + cost
            fees += cost
            hedge_trades.append(HedgeTrade(step * dt, stock_inventory, quantity, path[step], cost))
            stock_inventory = target_stock

    cash *= math.exp(state.rate * dt)
    payoff = contract.payoff(path[-1])
    final_equity = cash + stock_inventory * path[-1] + option_inventory * payoff
    residual_before_fees = final_equity + fees - spread_capture
    attribution = PnLAttribution(
        spread_capture=spread_capture,
        inventory_pnl=residual_before_fees,
        fees=fees,
    )
    return MarketMakerResult(
        final_equity=final_equity,
        terminal_spot=path[-1],
        option_inventory=option_inventory,
        stock_inventory=stock_inventory,
        accepted_orders=accepted,
        rejected_orders=rejected,
        attribution=attribution,
        hedge_trades=tuple(hedge_trades),
    )
