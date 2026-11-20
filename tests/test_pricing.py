import math
import unittest

from options_lab.models import MarketState, OptionContract, OptionType
from options_lab.monte_carlo import monte_carlo_price
from options_lab.pricing import binomial_price, black_scholes_greeks, black_scholes_price


class PricingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = MarketState(spot=100.0, rate=0.03, volatility=0.20)
        self.call = OptionContract(100.0, 0.5, OptionType.CALL)
        self.put = OptionContract(100.0, 0.5, OptionType.PUT)

    def test_put_call_parity(self) -> None:
        call = black_scholes_price(self.call, self.state)
        put = black_scholes_price(self.put, self.state)
        expected = self.state.spot - self.call.strike * math.exp(-self.state.rate * self.call.expiry_years)
        self.assertAlmostEqual(call - put, expected, places=10)

    def test_call_price_is_monotone_in_spot(self) -> None:
        low = black_scholes_price(self.call, MarketState(90.0, 0.03, 0.20))
        high = black_scholes_price(self.call, MarketState(110.0, 0.03, 0.20))
        self.assertGreater(high, low)
        self.assertGreaterEqual(low, 0.0)
        self.assertLessEqual(high, 110.0)

    def test_call_delta_is_between_zero_and_one(self) -> None:
        delta = black_scholes_greeks(self.call, self.state)["delta"]
        self.assertGreater(delta, 0.0)
        self.assertLess(delta, 1.0)

    def test_binomial_converges_to_black_scholes(self) -> None:
        analytical = black_scholes_price(self.call, self.state)
        approximate = binomial_price(self.call, self.state, steps=1_000)
        self.assertAlmostEqual(approximate, analytical, delta=0.02)

    def test_monte_carlo_interval_contains_analytical_price(self) -> None:
        analytical = black_scholes_price(self.call, self.state)
        estimate = monte_carlo_price(self.call, self.state, paths=50_000, seed=11)
        self.assertLessEqual(estimate.ci_low, analytical)
        self.assertGreaterEqual(estimate.ci_high, analytical)


if __name__ == "__main__":
    unittest.main()
