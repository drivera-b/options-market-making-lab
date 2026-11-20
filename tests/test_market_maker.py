import unittest

from options_lab.market_maker import make_quote, simulate_market_maker
from options_lab.models import MarketMakerPolicy, MarketState, OptionContract, OptionType


class MarketMakerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = OptionContract(100.0, 0.25, OptionType.CALL)
        self.state = MarketState(100.0, 0.02, 0.20)
        self.policy = MarketMakerPolicy(inventory_limit=2)

    def test_positive_inventory_lowers_reservation_quote(self) -> None:
        flat = make_quote(5.0, 0, self.policy)
        long_inventory = make_quote(5.0, 2, self.policy)
        self.assertLess(long_inventory.bid, flat.bid)
        self.assertLess(long_inventory.ask, flat.ask)

    def test_simulation_is_reproducible_and_reconciled(self) -> None:
        first = simulate_market_maker(self.contract, self.state, self.policy, steps=40, seed=13)
        second = simulate_market_maker(self.contract, self.state, self.policy, steps=40, seed=13)
        self.assertEqual(first, second)
        self.assertAlmostEqual(first.attribution.total, first.final_equity, places=10)

    def test_inventory_limit_is_enforced(self) -> None:
        result = simulate_market_maker(
            self.contract,
            self.state,
            self.policy,
            steps=80,
            order_probability=1.0,
            customer_buy_probability=1.0,
            seed=2,
        )
        self.assertLessEqual(abs(result.option_inventory), self.policy.inventory_limit)
        self.assertGreater(result.rejected_orders, 0)


if __name__ == "__main__":
    unittest.main()
