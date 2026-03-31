# Golemio Prague Tram Timetable (Starter)

Small CLI project that lists departures for selected tram lines from selected stops using the Golemio PID API.

## What it does

- Reads API key from `GOLEMIO_API_KEY` or from `secrets.txt`
- Calls `GET /v2/pid/departureboards`
- Filters results to trams (`route.type == 0`)
- Optionally filters to selected tram lines (for example `9,22,17`)
- Prints a simple table in terminal

## 1) Install dependencies

```bash
python3 -m venv golemio_venv
source golemio_venv/bin/activate
pip install -r requirements.txt
```

## 2) Create your config

```bash
cp config.example.json config.json
```

Edit `config.json` values:

- `stop_names`: exact stop names (case and whitespace sensitive according to API docs)
- `tram_lines`: line short names you want to track
- `minutes_after`: how far ahead to fetch departures

## 3) Run

```bash
python app.py
```

Override config quickly:

```bash
python app.py --stops "Anděl,Karlovo náměstí" --lines "9,22"
```

## API endpoint used

- Base URL: `https://api.golemio.cz`
- Endpoint: `/v2/pid/departureboards`
- Auth header: `X-Access-Token: <your-token>`

## Notes

- The API rate limit from docs is 20 requests per 8 seconds by default.
- If a stop name does not match exactly (including diacritics), the API can return `404`.
- To fetch by stop IDs instead of names later, we can extend this script easily.



To get vichicle positions:
```
https://api.golemio.cz/v2/vehiclepositions/gtfsrt/vehicle_positions.pb
```

