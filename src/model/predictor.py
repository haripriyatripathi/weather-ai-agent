"""turn a weather forecast into probabilities for each market temperature bucket."""
import math
import re

# typical error (in f) for a 1-day temperature forecast.
# real forecasts are off by roughly this much on average.
FORECAST_STD = 3.0


def _normal_cdf(x, mean, std):
    """probability that a normal(mean, std) value is <= x."""
    return 0.5 * (1 + math.erf((x - mean) / (std * math.sqrt(2))))


def bucket_probability(forecast_temp, low, high, std=FORECAST_STD):
    """probability the actual temp lands in [low, high], given our forecast."""
    return _normal_cdf(high, forecast_temp, std) - _normal_cdf(low, forecast_temp, std)


def parse_bucket(outcome_label):
    """pull a (low, high) range out of a market outcome label.

    handles labels like '81-82', '83 to 84', '90+', 'below 70'.
    returns none if no range can be read.
    """
    nums = [int(n) for n in re.findall(r"\d+", outcome_label)]
    label = outcome_label.lower()

    if not nums:
        return None
    if len(nums) >= 2:
        return (nums[0], nums[1])
    # single number
    n = nums[0]
    if "+" in label or "above" in label or "over" in label or "higher" in label:
        return (n, n + 100)      # open-ended upper bucket
    if "below" in label or "under" in label or "less" in label:
        return (n - 100, n)      # open-ended lower bucket
    return (n - 0.5, n + 0.5)    # exact value -> 1 degree window


def predict_market(forecast_temp, outcomes):
    """given a forecast and a market's outcomes, return our probability per outcome.

    outcomes: list of (label, market_price) tuples.
    returns: list of dicts with label, our probability, and the market price.
    """
    results = []
    for label, market_price in outcomes:
        rng = parse_bucket(label)
        if rng is None:
            our_prob = None
        else:
            our_prob = bucket_probability(forecast_temp, rng[0], rng[1])
        results.append({
            "label": label,
            "our_prob": our_prob,
            "market_price": market_price,
        })
    return results


if __name__ == "__main__":
    # quick self-test: forecast 82f, a few example buckets.
    example_outcomes = [
        ("80-81", 0.20),
        ("82-83", 0.35),
        ("84-85", 0.15),
    ]
    for r in predict_market(82.0, example_outcomes):
        prob = f"{r['our_prob']:.0%}" if r["our_prob"] is not None else "n/a"
        print(f"{r['label']:8} | our prob {prob:>5} | market {r['market_price']:.0%}")