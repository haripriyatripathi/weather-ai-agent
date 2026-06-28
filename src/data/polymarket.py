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
    try:
        outcomes = json.loads(market.get("outcomes", "[]"))
        prices = json.loads(market.get("outcomePrices", "[]"))
        return list(zip(outcomes, [float(p) for p in prices]))
    except (json.JSONDecodeError, ValueError):
        return []


def search_markets(query, limit=5):
    url = f"{GAMMA}/public-search"
    params = {"q": query, "limit_per_type": limit}
    r = requests.get(url, params=params, timeout=15,
                     headers={"User-Agent": "stormcaller/1.0"})
    r.raise_for_status()
    data = r.json()
    return data.get("markets", []) or data.get("events", [])


def get_weather_markets():
    results = {}
    for city, query in CITY_QUERIES.items():
        markets = search_markets(query)
        parsed = []
        for m in markets:
            outcomes = _parse_prices(m)
            parsed.append({
                "question": m.get("question") or m.get("title", "?"),
                "outcomes": outcomes,
                "closed": m.get("closed", None),
            })
        results[city] = parsed
    return results


if __name__ == "__main__":
    data = get_weather_markets()
    for city, markets in data.items():
        print(f"\n {city}")
        if not markets:
            print("  (no markets found)")
        for m in markets[:3]:
            print(f"  {m['question']}")
            for outcome, price in m["outcomes"]:
                print(f"      {outcome}: {price:.2f}")