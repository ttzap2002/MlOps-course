from fastmcp import FastMCP
import httpx
import os
from typing import Optional, Annotated
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
API_KEY = os.getenv("WEATHER_API")
mcp = FastMCP("Weather Server")

def get_coordinates(city: str, country: str, api_key: str) -> Optional[tuple[float, float]]:
    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {"q": f"{city},{country}", "limit": 1, "appid": api_key}

    try:
        response = httpx.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        return data[0]["lon"], data[0]["lat"]

    except Exception as e:
        print(f"Error fetching coordinates: {e}")
        return None

@mcp.tool(description="Get weather forecast for 5 days starting from today.")
def get_weather_forecast(city: Annotated[str, "Name of the city e.g. 'Paris'"],
                       country: Annotated[str, "Name of the country e.g. 'Italy'"]) -> str:
    url = "https://api.openweathermap.org/data/2.5/forecast"
    lat, lot = get_coordinates(city, country, API_KEY)
    params = {"lat": lat, "lon": lot, "appid": API_KEY, "units": "metric"}

    response = httpx.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    days_forecast = []
    for day in data["list"]:
        day_summary = {
            "date": datetime.fromtimestamp(day["dt"]).strftime("%Y-%m-%d"),
            "condition": day["weather"][0]["description"],
            "temp": {
                "day": day["main"]["temp"],
                "min": day["main"]["temp_min"],
                "max": day["main"]["temp_max"]
            },
            "humidity": day["main"]["humidity"]
        }
        days_forecast += [day_summary]

    return f"Weather forecast for {city}, {country}: {days_forecast}"

# Api hasn't worked due to lack of subscription
"""
@mcp.tool(description="Get weather forecast for the next 1-16 days starting from today.")
def get_daily_forecast(city: Annotated[str, "Name of the city e.g. 'Paris'"],
                       country: Annotated[str, "Name of the country e.g. 'Italy'"], days: Annotated[int, "A number of days, which will be returned "] = 1) -> str:

    if days < 1 or days > 16:
        raise ValueError("days must be between 1 and 16")

    url = "https://api.openweathermap.org/data/2.5/forecast/daily"
    lat, lot = get_coordinates(city, country, API_KEY)

    params = {"lat": lat, "lon": lot, "appid": API_KEY, "cnt": days}

    response = httpx.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    days_forecast = []
    for day in data.get("list", []):
        day_summary = {
            "date": datetime.fromtimestamp(day["dt"]).strftime("%Y-%m-%d"),
            "condition": day["weather"][0]["description"],
            "temp": {
                "day": day["temp"]["day"],
                "min": day["temp"]["min"],
                "max": day["temp"]["max"]
            },
            "rain_mm": day.get("rain", 0)
        }
        days_forecast += [day_summary]

    return f"Weather forecast for {city}, {country}: {days_forecast}"

@mcp.tool(description="Get monthly average weather for particular city")
def get_aggregated_weather(city: Annotated[str, "Name of the city e.g. 'Paris'"],
                           country: Annotated[str, "Name of the country e.g. 'Italy'"],
                           month: Annotated[int, "A number of the month in the year 1-12"]) -> str:

    if month < 1 or month > 16:
        raise ValueError("days must be between 1 and 16")

    url = "https://history.openweathermap.org/data/2.5/aggregated/month"
    lat, lot = get_coordinates(city, country, API_KEY)

    params = {"lat": lat, "lon": lot, "appid": API_KEY, "month": month}
    response = httpx.get(url, params=params)
    response.raise_for_status()
    data = response.json()["results"]


    return (f"Monthly weather for {city}, {country}: {data['main']['temp']}: \n"
            f"Average Temperature: {data['temp']['mean']}"
            f"Average Pressure: {data['pressure']['mean']} hPa"
            f"Average Wind Speed: {data['wind']['speed']} m/s"
            f"Average Humidity: {data['humidity']['mean']} %")
"""

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8001)


