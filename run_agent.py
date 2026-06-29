"""the runner: connects every piece and lets the agent place paper trades on its own.

flow per city:
  weather forecast -> find threshold markets -> model gives our probability
  -> compare to market price -> kelly decides stake -> place a paper order.

run normally:   python run_agent.py
demo mode:      python run_agent.py --demo      (lowers edge threshold)
verbose mode:   python run_agent.py --verbose   (shows reasoning for every market)
"""
import re
import sys
from src.data.weather_global import get_weather, CITIES
from src.data.polymarket import search_markets, extract_markets_from_event
from src.model.predictor import _normal_cdf, FORECAST_STD
from src.strategy.kelly import decide_bet
from src.trading.paper_trader import place_order, show_summary, _load_state

VERBOSE = False


def parse_threshold(question):
    """read a temperature threshold and direction from a yes/no question."""
    nums = re.findall(r"(\d+)\s*°?f", question.lower())
    if not nums:
        return None
    temp = int(nums[0])
    q = question.lower()
    if "below" in q or "under" in q or "less" in q:
        return (temp, "below")
    if "above" in q or "over" in q or "higher" in q or "greater" in q:
        return (temp, "above")
    return None


def our_yes_probability(forecast_high, temp, direction):
    """our probability that 'yes' happens, given our forecast."""
    p_below = _normal_cdf(temp, forecast_high, FORECAST_STD)
    return p_below if direction == "below" else (1 - p_below)


def find_threshold_markets(city):
    """get yes/no threshold markets (with prices) for this city."""
    events = search_markets(f"highest temperature {city}")
    markets = []
    for ev in events:
        markets.extend(extract_markets_from_event(ev))
    return markets


def run_once():
    """run one full pass over all tradable cities."""
    print(f"starting bankroll: ${_load_state()['bankroll']:.2f}\n")
    tradable = [c for c in CITIES if CITIES[c]["tradable"]]

    for city in tradable:
        print(f"--- {city} ---")
        forecast_high = get_weather(city)["high_f"]
        print(f"  forecast high: {forecast_high}F")

        markets = find_threshold_markets(city)
        if not markets:
            print("  no usable market found, skipping\n")
            continue

        placed_any = False
        for m in markets:
            parsed = parse_threshold(m["question"])
            if parsed is None:
                continue
            temp, direction = parsed

            yes_price = next((p for label, p in m["outcomes"]
                              if label.lower() == "yes"), None)
            if yes_price is None:
                continue

            our_prob = our_yes_probability(forecast_high, temp, direction)

            # in verbose mode, show our reasoning for this market
            if VERBOSE:
                short_q = m["question"][:50]
                print(f"    [{short_q}...]")
                print(f"      threshold {temp}F ({direction}) | "
                      f"our {our_prob:.0%} vs market {yes_price:.2f} "
                      f"| edge {our_prob - yes_price:+.2f}")

            if yes_price < 0.02 or yes_price > 0.98:
                if VERBOSE:
                    print("      -> skip (price at extreme, no liquidity)")
                continue

            decision = decide_bet(our_prob, yes_price, _load_state()["bankroll"])

            if decision["action"] == "buy":
                place_order(city, m["question"], "Yes", yes_price, decision["stake"])
                print(f"  BUY Yes @ {yes_price:.3f} | our {our_prob:.0%} "
                      f"| stake ${decision['stake']} | edge {decision['edge']:+.2f}")
                placed_any = True
            elif VERBOSE:
                print(f"      -> skip ({decision.get('reason', 'no edge')})")

        if not placed_any:
            print("  no edge big enough, no bet placed")
        print()

    print("=" * 40)
    show_summary()


if __name__ == "__main__":
    if "--verbose" in sys.argv:
        VERBOSE = True
        print(">>> VERBOSE MODE: showing the agent's reasoning for every market <<<\n")
    if "--demo" in sys.argv:
        import src.strategy.kelly as kelly
        kelly.MIN_EDGE = 0.0
        print(">>> DEMO MODE: edge threshold lowered to show live trading <<<\n")
    run_once()