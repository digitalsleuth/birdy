# birdy
A short python3 script to parse the JSON ride data from the Bird Electric Scooter app.

## Usage

```bash
Bird Scooter Ride JSON parser v1.0.0

positional arguments:
  file                  Ride JSON file

options:
  -h, --help            show this help message and exit
  -d DATE, --date DATE  Specific date to filter on - 'YYYY-MM-DD'
  -k, --kml             Output a KML file
  -l, --list            List available timezones
  -p, --psv             Output a Pipe (|) Separated Value (.psv) file
  -t TZ, --tz TZ        Select a timezone for output, in quotes: 'TZ_NAME'
```
