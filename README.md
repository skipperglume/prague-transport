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




## Getting geojson about prague administrative and municipal districts
```bash
curl "https://services1.arcgis.com/LPm07959azIAvFRD/ArcGIS/rest/services/MAP_CUR_MAP_MESTSKECASTI_P/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson" -o prague_districts.geojson
```



[Praha 10], [Praha 10]
[Praha 5], [Praha 5]
[Praha 2], [Praha 2]
[Praha 8], [Praha 8]
[Praha 15], [Praha 15]
[Praha 4], [Praha 4]
[Praha 22], [Praha 22]
[Praha 17], [Praha 17]
[Praha 1], [Praha 1]
[Praha 14], [Praha 14]
[Praha 3], [Praha 3]
[Praha 7], [Praha 7]
[Praha 9], [Praha 9]
[Praha 20], [Praha 20]
[Praha 19], [Praha 19]
[Praha 6], [Praha 6]
[Praha 18], [Praha 18]
[Praha 21], [Praha 21]
[Praha 13], [Praha 13]
[Praha 12], [Praha 12]
[Praha 11], [Praha 11]
[Praha 16], [Praha 16]