"""decide whether to bet and how much, using edge and the kelly criterion."""

# minimum edge before we bother placing a bet (5 percentage points).
# below this, the gap is likely just noise, not a real mispricing.
MIN_EDGE = 0.05

# we bet half of what full kelly suggests. full kelly is too swingy,
# so half-kelly is the standard risk-managed choice.
KELLY_FRACTION = 0.5


def edge(our_prob, market_price):
    """how much our probability beats the market price. positive = we like the bet."""
    return our_prob - market_price


def kelly_fraction(our_prob, market_price):
    """fraction of bankroll to bet on a 'yes' at the given price.

    formula: (q - p) / (1 - p), where q is our probability and p is the price.
    returns 0 if there's no positive edge.
    """
    if market_price >= 1 or market_price <= 0:
        return 0.0
    raw = (our_prob - market_price) / (1 - market_price)
    return max(0.0, raw)


def decide_bet(our_prob, market_price, bankroll):
    """decide if and how much to bet on one outcome.

    returns a dict describing the decision.
    """
    e = edge(our_prob, market_price)

    if e < MIN_EDGE:
        return {"action": "skip", "reason": "edge too small",
                "edge": e, "stake": 0.0}

    full_kelly = kelly_fraction(our_prob, market_price)
    safe_fraction = full_kelly * KELLY_FRACTION
    stake = round(bankroll * safe_fraction, 2)

    return {
        "action": "buy",
        "edge": round(e, 3),
        "kelly_fraction": round(safe_fraction, 3),
        "stake": stake,
    }


if __name__ == "__main__":
    bankroll = 1000.0
    # a few test cases: (our prob, market price)
    tests = [
        (0.70, 0.50),   # big edge -> should bet
        (0.55, 0.52),   # tiny edge -> should skip
        (0.40, 0.60),   # market thinks more likely than us -> skip
    ]
    for q, p in tests:
        d = decide_bet(q, p, bankroll)
        print(f"our {q:.0%} vs market {p:.0%} -> {d}")