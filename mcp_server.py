"""mcp server: exposes the weather-trading agent's functions as tools an llm can call.

run it standalone to test, or connect it to hermes (or any mcp client) so the
agent can: get a forecast, list weather markets, evaluate a trade, and place one.
"""
from mcp.server.fastmcp import FastMCP

from src.data.weather_global import get_weather, CITIES
from src.data.polymarket import search_markets, extract_markets_from_event
from src.model.predictor import _normal_cdf, FORECAST_STD
from src.strategy.kelly import decide_bet
from src.trading.paper_trader import place_order, show_summary, _load_state

mcp = FastMCP("weather-trading-agent")


@mcp.tool()
def get_forecast(city: str) -> dict:
    """get today's weather forecast (high/low temp) for a city.

    valid cities: New York, Los Angeles, Chicago, Miami, Houston, Mumbai, Delhi, Tokyo.
    """
    if city not in CITIES:
        return {"error": f"unknown city. choose from: {', '.join(CITIES)}"}
    return get_weather(city)


@mcp.tool()
def get_weather_markets(city: str) -> list:
    """list current polymarket weather markets (with yes/no prices) for a city."""
    events = search_markets(f"highest temperature {city}")
    markets = []
    for ev in events:
        markets.extend(extract_markets_from_event(ev))
    # trim to a readable summary
    return [{"question": m["question"], "outcomes": m["outcomes"]} for m in markets[:10]]


@mcp.tool()
def evaluate_trade(our_probability: float, market_price: float) -> dict:
    """given our probability and the market price, decide whether/how much to bet.

    uses edge + half-kelly sizing against the current bankroll.
    """
    bankroll = _load_state()["bankroll"]
    return decide_bet(our_probability, market_price, bankroll)


@mcp.tool()
def place_trade(city: str, question: str, outcome: str,
                price: float, stake: float) -> dict:
    """place a paper (simulated) trade and record it. no real money is used."""
    return place_order(city, question, outcome, price, stake)


@mcp.tool()
def portfolio_summary() -> dict:
    """return the current bankroll, open positions, and realized p&l."""
    state = _load_state()
    total_profit = round(sum(h["profit"] for h in state["history"]), 2)
    return {
        "bankroll": state["bankroll"],
        "open_positions": len(state["positions"]),
        "closed_bets": len(state["history"]),
        "total_pnl": total_profit,
        "positions": state["positions"],
    }


if __name__ == "__main__":
    mcp.run()