"""backtest the strategy on real past weather to produce honest statistics.

method:
  - for each past day we know the actual high temp (open-meteo archive = ground truth).
  - we and the market both see the same noisy signal of that temp, but our forecast
    is slightly sharper -- a small, realistic edge, not a fabricated one.
  - the agent trades, then we resolve against the actual temp.
  - any single bet is capped at a small fraction of bankroll for risk control.

limitation: historical polymarket prices are not available, so the market is
simulated. the test shows whether a small forecasting edge survives kelly sizing.
"""
import random
import requests
from datetime import date, timedelta

from src.data.weather_global import CITIES
from src.model.predictor import _normal_cdf
from src.strategy.kelly import decide_bet

ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"

random.seed(42)
OUR_STD = 3.0
MARKET_STD = 3.3
MAX_BET_FRACTION = 0.03
DAYS_BACK = 30
STARTING_BANKROLL = 1000.0


def get_actual_highs(city, start, end):
    coords = CITIES[city]
    params = {
        "latitude": coords["lat"],
        "longitude": coords["lon"],
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "temperature_2m_max",
        "temperature_unit": "fahrenheit",
        "timezone": coords["tz"],
    }
    r = requests.get(ARCHIVE, params=params, timeout=30)
    r.raise_for_status()
    daily = r.json()["daily"]
    return list(zip(daily["time"], daily["temperature_2m_max"]))


def run_backtest():
    end = date.today() - timedelta(days=2)
    start = end - timedelta(days=DAYS_BACK)

    bankroll = STARTING_BANKROLL
    trades = wins = 0
    pnl = 0.0
    tradable = [c for c in CITIES if CITIES[c]["tradable"]]

    for city in tradable:
        for day, actual_high in get_actual_highs(city, start, end):
            if actual_high is None:
                continue

            threshold = round(actual_high) + random.choice([-3, -2, -1, 1, 2, 3])

            shared_signal = actual_high + random.gauss(0, 2.5)
            forecast = shared_signal + random.gauss(0, 0.5)
            our_prob_yes = 1 - _normal_cdf(threshold, forecast, OUR_STD)

            market_est = shared_signal + random.gauss(0, 1.5)
            market_prob_yes = 1 - _normal_cdf(threshold, market_est, MARKET_STD)
            market_price = min(0.98, max(0.02, market_prob_yes))

            decision = decide_bet(our_prob_yes, market_price, bankroll)
            if decision["action"] != "buy":
                continue

            stake = min(decision["stake"], bankroll * MAX_BET_FRACTION)
            if stake <= 0:
                continue

            shares = stake / market_price
            trades += 1
            bankroll -= stake

            won = actual_high >= threshold
            if won:
                bankroll += shares
                pnl += shares - stake
                wins += 1
            else:
                pnl -= stake

    print("backtest results")
    print(f"period             {start} to {end}")
    print(f"cities             {', '.join(tradable)}")
    print(f"trades placed      {trades}")
    if trades:
        print(f"wins               {wins}  ({wins / trades:.0%} win rate)")
    print(f"starting bankroll  ${STARTING_BANKROLL:.2f}")
    print(f"ending bankroll    ${bankroll:.2f}")
    print(f"total p&l          ${pnl:+.2f}")
    print(f"roi                {pnl / STARTING_BANKROLL:+.1%}")


if __name__ == "__main__":
    run_backtest()