import csv
import requests
import pandas as pd
import argparse
import logging
import unicodedata
import os
from tabulate import tabulate
from datetime import datetime

#Config Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger=logging.getLogger(__name__)

def load_cities(path_csv):
    logger.info(f"Loading cities from:  {path_csv}")
    df = pd.read_csv(path_csv)
    logger.info(f"CSV loaded successfully - {len(df)} cities found")
    return df

def normalize_city(text):
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text

def search_city(df,name):
    normalize_name = normalize_city(name)
    results = df[df["city"].apply(lambda x: normalize_city(str(x))).str.contains(normalize_name, na=False)]
    results = results.sort_values("population", ascending=False)
    logger.info(f"Search '{name}' - {len(results)} result(s) found")
    return results

def select_city(results, name_input):
    if results.empty:
        logger.warning(f"No results found for '{name_input}'")
        return None

    if len(results) == 1:
        city = results.iloc[0]
        logger.info(f"Single result - auto-selected: {city['city']}, {city['country']}")
        return city
    
    print (f"\n{len(results)} cities found:\n")
    for i, (_, row) in enumerate(results.iterrows()):
        population = f"{int(row['population']):,}" if pd.notna(row['population']) else "unknown"
        print(f" [{i+1}] {row['city']}, {row['country']} - {row['admin_name']} - Population: {population}")
    

    print()
    while True:
        selection = input(f"Choose a number: (1 - {len(results)}):").strip()
        if selection.isdigit() and 1 <= int(selection) <= len(results):
            city = results.iloc[int(selection) - 1]
            logger.info(f"User selected: {city['city']}, {city['country']}")
            return city
        logger.warning(f"Invalid input: '{selection}' - Please try again")

def obtain_weather(city):
    lat = city["lat"]
    lon = city["lng"]
    name = city["city"]
    country = city["country"]

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current_weather=true"
        f"&hourly=relative_humidity_2m,apparent_temperature"
    )

    logger.info(f"Fetching weather for {name}, {country} - URL: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.ConnectionError:
        logger.error("No internet connection - Unable to fetch weather data")
        return None
    except requests.exceptions.Timeout:
        logger.error("The API took too long to respond")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error HTTP: {e}")
        return None
    
    #Extract current weather to normalize time

    cw = data["current_weather"]

    current_hour = cw["time"][:13] + ":00"

    #Find matching hour in hourly data - if not found, use index 0 and log a warning

    try:
        index = data["hourly"]["time"].index(current_hour)
    except ValueError:
        logger.warning("Current hour not found in hourly data - using index 0")
        index = 0
    
    return {
    "city": name,
    "country": country,
    "temperature_c": cw["temperature"],
    "windspeed_kmh": cw["windspeed"],
    "winddirection": wind_direction(cw["winddirection"]),
    "is_day": day_night(cw["is_day"]),
    "apparent_temperature_c": data["hourly"]["apparent_temperature"][index],
    "relative_humidity_pct": data["hourly"]["relative_humidity_2m"][index], 
    }

def save_historical(weather, output_path):
    file_exists = os.path.exists(output_path)

    with open(output_path, "a", encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=weather.keys())
        if not file_exists:
            writer.writeheader()

        writer.writerow(weather)
        logger.info(f"Result saved to {output_path}")


def day_night(is_day):    return "Day" if is_day == 1 else "Night"

def wind_direction(deg):
    cardinals = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    car_index = int((deg + 22.5) % 360 // 45)
    return cardinals[car_index]

def show_table(weather):
    chart = tabulate([weather.values()], headers=weather.keys(), tablefmt="rounded_outline")
    print(chart)



def main(args):
    df = load_cities(args.input)

    city_input = input("Enter the name of the city: ").strip()

    if not city_input:
        logger.error("No city name entered. Closing the script.")
        return
    
    if len(city_input) < 2:
        logger.error("Enter at least 2 characters to search.")
        return

    results = search_city(df, city_input)
    city = select_city(results, city_input)

    if city is None:
        return
    
    weather = obtain_weather(city)
    
    if weather is None:
        logger.error("No weather data obtained - Aborting")
        return
    
    weather["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    show_table(weather)

    save_historical(weather, args.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weather pipeline for city")
    parser.add_argument("--input", required=True, help="CSV Cities file path")
    parser.add_argument("--output", required=True, help="CSV output file path")
    args = parser.parse_args()
    main(args)






