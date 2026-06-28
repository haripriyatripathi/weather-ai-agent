"""fetch weather prediction markets from polymarket (gamma api, public, no key)."""
import json
import requests

GAMMA = "https://gamma-api.polymarket.com"

CITY_QUERIES = {
    "New York":    "temperature NYC",
    "Los Angeles": "temperature Los Angeles",
    "Chicago":     "temperature Chicago",
    "Miami":       "temperature Miami",
    "Houston":     "temperature Houston",
}


def _parse_prices(market):
    """polymarket returns outcomes/prices as json-encoded strings. decode them."""
    try:
        outcomes = json.loads(market.get("outcomes", "[]"))
        prices = json.loads(market.get("outcomePrices", "[]"))
        return list(zip(outcomes, [float(p) for p in prices]))
    except (json.JSONDecodeError, ValueError):
        return []


def extract_markets_from_event(event):
    """events wrap a list of markets. pull out each market with its prices."""
    out = []
    for m in event.get("markets", []):
        outcomes = _parse_prices(m)
        if outcomes:
            out.append({
                "question": m.get("question") or event.get("title", "?"),
                "outcomes": outcomes,
            })
    return out


def search_markets(query, limit=5):
    """search polymarket for events matching a query string."""
    url = f"{GAMMA}/public-search"
    params = {"q": query, "limit_per_type": limit}
    r = requests.get(url, params=params, timeout=15,
                     headers={"User-Agent": "stormcaller/1.0"})
    r.raise_for_status()
    data = r.json()
    return data.get("events", []) or data.get("markets", [])


def get_weather_markets():
    """return weather markets (with prices) for each tradable city."""
    results = {}
    for city, query in CITY_QUERIES.items():
        events = search_markets(query)
        parsed = []
        for ev in events:
            parsed.extend(extract_markets_from_event(ev))
        results[city] = parsed
    return results


if __name__ == "__main__":
    data = get_weather_markets()
    for city, markets in data.items():
        print(f"\n--- {city} ---")
        if not markets:
            print("  (no markets found)")
        for m in markets[:3]:
            print(f"  {m['question']}")
            for outcome, price in m["outcomes"]:
                print(f"      {outcome}: {price:.2f}")