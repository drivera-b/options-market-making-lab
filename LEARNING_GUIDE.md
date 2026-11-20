# Learning Guide

Spend two to four hours on each stage. Do the handwritten exercise before reading or modifying the corresponding code.

## 1. Payoffs and no-arbitrage

By hand:

- Draw call and put payoffs at expiration.
- Explain why a European call cannot be worth more than the stock.
- Verify `call - put = spot - strike * exp(-rate * time)` for one example.

Code: `OptionContract.payoff` and `black_scholes_price`.

Exit test: explain put-call parity without memorized wording.

## 2. One-period binomial hedge

For stock outcomes `Su` and `Sd` with option payoffs `Cu` and `Cd`, solve:

`delta = (Cu - Cd) / (Su - Sd)`

Then solve for the cash position that reproduces the option in both states.

Code: `binomial_price`.

Exit test: derive delta and explain why risk-neutral probability is a pricing device, not a prediction.

## 3. Black–Scholes and Greeks

Focus on assumptions and sensitivities before attempting a full stochastic-calculus derivation.

- Delta: local price sensitivity and hedge ratio
- Gamma: how quickly delta changes
- Vega: sensitivity to volatility
- Theta: time decay under the model
- Rho: sensitivity to the risk-free rate

Code: `black_scholes_price` and `black_scholes_greeks`.

Exit test: predict how a call's price and delta change when spot or volatility rises.

## 4. Monte Carlo

Explain why discounted risk-neutral payoffs estimate the option value. Run the demo at several path counts and record how the confidence interval changes.

Code: `monte_carlo_price`.

Exit test: distinguish simulation error from model error.

## 5. Discrete delta hedging

Compare 12, 52, and 252 rebalances with identical seeds. Then add costs and make actual volatility differ from pricing volatility.

Code: `simulate_delta_hedge`.

Exit test: explain why more frequent hedging can reduce discretization error while increasing costs.

## 6. Market making

Trace cash, option inventory, stock inventory, and terminal value for five steps by hand.

Code: `make_quote` and `simulate_market_maker`.

Exit test: explain how a spread, inventory skew, hedge threshold, and inventory limit affect behavior.

## 7. Research discipline

Before each experiment, write:

- hypothesis
- frozen parameters
- primary metric
- failure criterion
- result
- limitation

Do not add machine learning until you can defend the analytical baselines. A future ML volatility or adverse-selection model must use chronological splits and beat an EWMA or other transparent baseline after costs.
