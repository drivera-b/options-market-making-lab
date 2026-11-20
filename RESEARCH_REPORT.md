# Research Report Template

## Research question

How do pricing assumptions, discrete hedging, transaction costs, spreads, and inventory limits affect an options market maker's simulated P&L?

## Baselines

- Black–Scholes analytical price
- Cox–Ross–Rubinstein binomial price
- Risk-neutral Monte Carlo estimate
- Delta hedge using model volatility

## Experiments to complete

| Experiment | Frozen comparison | Primary measurement | Failure criterion |
|---|---|---|---|
| Pricing convergence | Same contract and state | Absolute error vs. Black–Scholes | Error does not shrink with computation |
| Hedge frequency | Same generated path | Final hedge error and costs | Claimed improvement disappears after costs |
| Volatility mismatch | Same path and rebalance rule | Hedge error distribution | Result depends on one seed |
| Inventory skew | Same order-flow seeds | Inventory, rejects, P&L attribution | Lower inventory only comes from rejecting nearly everything |
| Spread sensitivity | Same order-flow seeds | Spread capture and total P&L | Wider spread assumes unchanged fill probability |

## Current limitations

- Geometric Brownian motion omits jumps, stochastic volatility, and volatility smiles.
- European exercise ignores early-exercise behavior.
- Random order flow omits informed trading and realistic fill probabilities.
- Black–Scholes Greeks inherit the assumptions of the pricing model.
- A simulated positive P&L is not evidence of a tradable edge.

## Honest conclusion format

1. State what changed inside the simulator.
2. State which assumptions caused the change.
3. State what evidence would be required before generalizing.
4. Include negative or inconclusive results.
