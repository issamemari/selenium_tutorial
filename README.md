# Tennis Booker

Tennis booker is a tool that automatically books a municipal tennis court in Paris.

## How it works

Tennis Booker uses Selenium to interact with the tennis court booking website. It uses a headless Chrome browser to simulate a user booking a court. It runs multiple processes in parallel that constantly check whether the required court is available. When a court is available, it books it.

A list of usernames and passwords are stored in `data.json`. The booker requires that the user has bought a carnet of 10 tennis courts, otherwise it will not work as payment would be required.

## Installation

Simply build the Docker image:

```
docker build -t booker .
```

## Usage

```
docker run booker --help
usage: main.py [-h] [--data DATA] [--tennis-facility TENNIS_FACILITY]
               [--location {indoor,outdoor}]
               [--surface-type {synthetique,beton_poreux}]
               [--court-id COURT_ID] [--username USERNAME] --date DATE --time
               TIME [--workers WORKERS] [--headless] [--logger-pretty]

optional arguments:
  -h, --help            show this help message and exit
  --data DATA
  --tennis-facility TENNIS_FACILITY
                        Name of the tennis facility. If not specified, all
                        tennis facilities will be considered.
  --location {indoor,outdoor}
                        Location (indoor or outdoor). If not specified, both
                        will be considered.
  --surface-type {synthetique,beton_poreux}
                        Surface type (synthetique or beton_poreux). If not
                        specified, both will be considered.
  --court-id COURT_ID   Court ID. If not specified, all courts will be
                        considered.
  --username USERNAME   Username. If not specified, all users will be used.
  --date DATE           format: 01/01/2022
  --time TIME           format: 08h
  --workers WORKERS
  --headless
  --logger-pretty
```

## Example

Book an indoor court with synthetic surface on 24/09/2022 at 9pm using 16 workers from user issa.memari@gmail.com:

```
docker run booker --date 24/09/2022 --time 21h --location indoor --surface-type synthetique --workers 16 --username issa.memari@gmail.com
```

## Supported Tennis Facilities and Courts

| Tennis Facility | Indoor Courts | Outdoor Courts |
| --------------- | ------------- | -------------- |
| Elisabeth       | 4             | 0              |

New facilities and courts can be added by modifying `data.json`.
