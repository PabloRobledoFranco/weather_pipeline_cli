# weather-pipeline-cli

A Python CLI pipeline that allows users to search for cities from a dataset and retrieve real-time weather information using the Open-Meteo API.

## Tech Stack
- Python 3.x
- pandas — CSV reading and filtering
- requests — API calls
- tabulate — terminal table formatting
- argparse — command-line arguments
- Open-Meteo API — free, no API key required

## Installation

1. Clone this repository:
   git clone https://github.com/PabloRobledoFranco/weather_pipeline_cli.git

2. Install dependencies:
   pip install -r requirements.txt

3. Download the city dataset from simplemaps:
   https://simplemaps.com/data/world-cities
   Place the CSV file inside the /data folder.

## How to run

```bash
python weather_pipeline.py --input data/worldcities.csv --output output/weather_history.csv
```

After starting the program:
1. Enter a city name
2. If multiple cities match, select one from the numbered list
3. The weather data will be displayed in the terminal and saved to the output CSV

## Output fields

| Field | Description |
|---|---|
| city | City name |
| country | Country |
| temperature_c | Current temperature (°C) |
| windspeed_kmh | Wind speed (km/h) |
| winddirection | Cardinal wind direction (N, NE, E...) |
| is_day | Day or Night |
| apparent_temperature_c | Feels like temperature (°C) |
| relative_humidity_pct | Relative humidity (%) |
| timestamp | Date and time of the query |

## Data sources

**City dataset** — World Cities Database by simplemaps  
https://simplemaps.com/data/world-cities  
Contains city names, countries, administrative regions, population and coordinates.

**Weather data** — Open-Meteo API  
https://open-meteo.com/  
Free API, no key required. Provides current temperature, wind speed, wind direction, apparent temperature and relative humidity.