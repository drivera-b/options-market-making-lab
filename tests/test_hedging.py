import unittest

from options_lab.hedging import geometric_brownian_path, simulate_delta_hedge
from options_lab.models import MarketState, OptionContract, OptionType


class HedgingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = OptionContract(100.0, 0.5, OptionType.CALL)
        self.state = MarketState(100.0, 0.03, 0.20)

    def test_seeded_path_is_reproducible(self) -> None:
        first = geometric_brownian_path(self.state, horizon_years=0.5, steps=12, seed=3)
        second = geometric_brownian_path(self.state, horizon_years=0.5, steps=12, seed=3)
        self.assertEqual(first, second)

    def test_attribution_reconciles_to_equity(self) -> None:
        result = simulate_delta_hedge(
            self.contract,
            self.state,
            steps=52,
            transaction_cost_rate=0.0002,
            seed=5,
        )
        self.assertAlmostEqual(result.attribution.total, result.final_equity, places=10)

    def test_costs_reduce_same_path_equity(self) -> None:
        no_cost = simulate_delta_hedge(self.contract, self.state, steps=52, seed=9)
        with_cost = simulate_delta_hedge(
            self.contract,
            self.state,
            steps=52,
            transaction_cost_rate=0.001,
            seed=9,
        )
        self.assertLess(with_cost.final_equity, no_cost.final_equity)


if __name__ == "__main__":
    unittest.main()
