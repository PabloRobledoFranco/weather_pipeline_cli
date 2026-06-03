import csv
import requests
import pandas as pd
import argparse
import logging
import unicodedata
import os
from tabulate import tabulate
from datetime import datetime

#Config del Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger=logging.getLogger(__name__)

def load_cities(path_csv):
    logger.info(f"Esta cargando las ciudades desde: {path_csv}")
    df = pd.read_csv(path_csv)
    logger.info(f"CSV cargado exitosamente - {len(df)} ciudades encontradas")
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
    logger.info(f"Busqueda '{name} - {len(results)} resultado(s) encontrado(s)")
    return results

def select_city(results, name_input):
    if results.empty:
        logger.warning(f"No se encontraron resultados para '{name_input}'")
        return None

    if len(results) == 1:
        city = results.iloc[0]
        logger.info(f"Un solo resultado - seleccionado automaticamente: {city['city']}, {city['country']}")
        return city
    
    print (f"\nSe encontraron {len(results)} ciudades: \n")
    for i, (_, row) in enumerate(results.iterrows()):
        population = f"{int(row['population']):,}" if pd.notna(row['population']) else "unknown"
        print(f" [{i+1}] {row['city']}, {row['country']} - {row['admin_name']} - Poblacion: {population}")
    

    print()
    while True:
        selection = input(f"Elige un numero: (1 - {len(results)}):").strip()
        if selection.isdigit() and 1 <= int(selection) <= len(results):
            city = results.iloc[int(selection) - 1]
            logger.info(f"El usuario ha seleccionado: {city['city']}, {city['country']}")
            return city
        logger.warning(f"Entrada invalida: '{selection}' - Intenta de nuevo")

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

    logger.info(f"Llamando a la API para la busqueda de la temperatura de {name}, {country}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.ConnectionError:
        logger.error("No hay conexion a internet")
        return None
    except requests.exceptions.Timeout:
        logger.error("La Api tardo mucho en responder")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error HTTP: {e}")
        return None
    
    #Extraemos Current Weather para normalizar el tiempo
    cw = data["current_weather"]

    current_hour = cw["time"][:13] + ":00"

    #Buscador de la hora en Hourly

    try:
        index = data["hourly"]["time"].index(current_hour)
    except ValueError:
        logger.warning("No se encontro la hora actual en hourly - usando indice 0")
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
        logger.info(f"Resultado guardado en {output_path}")


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

    city_input = input("Escribe el nombre de la ciudad de la cual quieres consultar el clima: ").strip()

    if not city_input:
        logger.error("No escribiste ningún nombre. Cerrando el script.")
        return
    
    if len(city_input) < 2:
        logger.error("Escribe al menos 2 caracteres para buscar.")
        return

    results = search_city(df, city_input)
    city = select_city(results, city_input)

    if city is None:
        return
    
    weather = obtain_weather(city)
    
    if weather is None:
        logger.error("No se pudo obtener el clima - Abortando")
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

#python CSVyAPI/weather_pipeline.py --input CSVyAPI/worldcities_copy.csv --output CSVyAPI/weather_results.csv




