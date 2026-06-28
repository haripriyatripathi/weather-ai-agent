"""Fetch weather data from Open-Meteo (free, no API key needed)."""
import requests

CITIES = {
    "New York":    {"lat": 40.7128, "lon": -74.0060, "tz": "America/New_York", "tradable": True},
    "Los Angeles": {"lat": 34.0522, "lon": -118.2437, "tz": "America/Los_Angeles", "tradable": True},
    "Chicago":     {"lat": 41.8781, "lon": -87.6298, "tz": "America/Chicago", "tradable": True},
    "Miami":       {"lat": 25.7617, "lon": -80.1918, "tz": "America/New_York", "tradable": True},
    "Houston":     {"lat": 29.7604, "lon": -95.3698, "tz": "America/Chicago", "tradable": True},
    "Mumbai":      {"lat": 19.0760, "lon": 72.8777, "tz": "Asia/Kolkata", "tradable": False},
    "Delhi":       {"lat": 28.7041, "lon": 77.1025, "tz": "Asia/Kolkata", "tradable": False},
    "Tokyo":       {"lat": 35.6762, "lon": 139.6503, "tz": "Asia/Tokyo", "tradable": False},
}


def get_weather(city):
    coords = CITIES[city]
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": coords["lat"],
        "longitude": coords["lon"],
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "temperature_unit": "fahrenheit",
        "timezone": coords["tz"],
        "forecast_days": 1,
    }
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    daily = response.json()["daily"]
    return {
        "city": city,
        "date": daily["time"][0],
        "high_f": daily["temperature_2m_max"][0],
        "low_f": daily["temperature_2m_min"][0],
        "precip": daily["precipitation_sum"][0],
        "tradable": coords["tradable"],
    }


def get_all_weather():
    return [get_weather(city) for city in CITIES]


if __name__ == "__main__":
    for w in get_all_weather():
        tag = "TRADABLE" if w["tradable"] else "scale-demo"
        print(f"{w['city']:13} | High {w['high_f']}F | Low {w['low_f']}F | Precip {w['precip']}mm | {w['date']} | {tag}")
