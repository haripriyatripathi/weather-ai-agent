"""simple paper-trading engine: places fake orders and tracks bankroll and p&l."""
import json
import os
from datetime import datetime

# where we save the running state (bankroll + open positions + history).
STATE_FILE = "data/paper_state.json"

STARTING_BANKROLL = 1000.0


def _load_state():
    """load saved state from disk, or start fresh if none exists."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "bankroll": STARTING_BANKROLL,
        "positions": [],   # open bets waiting to resolve
        "history": [],     # closed bets with outcomes
    }


def _save_state(state):
    """write state to disk so it survives between runs."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def place_order(city, question, outcome, price, stake):
    """place a simulated buy order on one outcome.

    buys `stake` worth of shares at `price`. shares = stake / price.
    """
    state = _load_state()

    if stake > state["bankroll"]:
        return {"error": "not enough bankroll", "bankroll": state["bankroll"]}

    shares = round(stake / price, 2)
    state["bankroll"] = round(state["bankroll"] - stake, 2)

    position = {
        "city": city,
        "question": question,
        "outcome": outcome,
        "price": price,
        "stake": stake,
        "shares": shares,
        "placed_at": datetime.now().isoformat(timespec="seconds"),
        "status": "open",
    }
    state["positions"].append(position)
    _save_state(state)
    return position


def resolve_position(index, won):
    """close an open position. if `won`, each share pays $1, else $0."""
    state = _load_state()
    if index >= len(state["positions"]):
        return {"error": "no such position"}

    pos = state["positions"].pop(index)
    payout = round(pos["shares"] * 1.0, 2) if won else 0.0
    profit = round(payout - pos["stake"], 2)

    state["bankroll"] = round(state["bankroll"] + payout, 2)
    pos["status"] = "won" if won else "lost"
    pos["payout"] = payout
    pos["profit"] = profit
    state["history"].append(pos)
    _save_state(state)
    return pos


def show_summary():
    """print current bankroll, open positions, and total p&l."""
    state = _load_state()
    total_profit = round(sum(h["profit"] for h in state["history"]), 2)
    print(f"bankroll: ${state['bankroll']:.2f}")
    print(f"open positions: {len(state['positions'])}")
    print(f"closed bets: {len(state['history'])}  | total p&l: ${total_profit:+.2f}")
    for p in state["positions"]:
        print(f"  OPEN  {p['city']:11} | {p['outcome']:8} @ {p['price']:.2f} | stake ${p['stake']}")


if __name__ == "__main__":
    # quick demo: place a bet, then resolve it as a win.
    print("placing a test order...")
    place_order("New York", "highest temp in NYC?", "82-83", 0.50, 200.0)
    show_summary()
    print("\nresolving it as a win...")
    resolve_position(0, won=True)
    show_summary()