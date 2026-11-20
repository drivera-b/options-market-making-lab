from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .hedging import simulate_delta_hedge
from .market_maker import simulate_market_maker
from .models import MarketMakerPolicy, MarketState, OptionContract, OptionType
from .monte_carlo import monte_carlo_price
from .pricing import binomial_price, black_scholes_greeks, black_scholes_price


def run_demo(seed: int = 7) -> dict[str, object]:
    contract = OptionContract(strike=100.0, expiry_years=0.5, option_type=OptionType.CALL)
    state = MarketState(spot=100.0, rate=0.03, volatility=0.20)
    analytical = black_scholes_price(contract, state)
    monte_carlo = monte_carlo_price(contract, state, paths=25_000, seed=seed)

    hedging_results = {}
    for steps in (12, 52, 252):
        result = simulate_delta_hedge(
            contract,
            state,
            steps=steps,
            transaction_cost_rate=0.0001,
            seed=seed,
        )
        hedging_results[str(steps)] = {
            "final_equity": result.final_equity,
            "fees": result.attribution.fees,
            "hedge_trades": len(result.trades),
        }

    market_maker = simulate_market_maker(
        contract,
        state,
        MarketMakerPolicy(),
        steps=52,
        seed=seed,
    )
    market_maker_summary = {
        "final_equity": market_maker.final_equity,
        "terminal_spot": market_maker.terminal_spot,
        "option_inventory": market_maker.option_inventory,
        "stock_inventory": market_maker.stock_inventory,
        "accepted_orders": market_maker.accepted_orders,
        "rejected_orders": market_maker.rejected_orders,
        "hedge_trade_count": len(market_maker.hedge_trades),
        "attribution": {
            **asdict(market_maker.attribution),
            "total": market_maker.attribution.total,
        },
    }
    return {
        "research_question": "How do model and market frictions affect simulated option market-making P&L?",
        "seed": seed,
        "contract": asdict(contract),
        "market_state": asdict(state),
        "pricing": {
            "black_scholes": analytical,
            "binomial_500_steps": binomial_price(contract, state, steps=500),
            "monte_carlo": asdict(monte_carlo),
            "greeks": black_scholes_greeks(contract, state),
        },
        "delta_hedging_by_rebalance_steps": hedging_results,
        "market_maker": market_maker_summary,
        "limitations": [
            "Geometric Brownian motion is a simplified price process.",
            "Order flow is random and does not model adverse selection.",
            "The simulator makes no claim of real-world profitability.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run reproducible options laboratory experiments.")
    parser.add_argument("--out", default="reports/demo_results.json")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)

    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(run_demo(args.seed), indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {destination.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
