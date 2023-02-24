# tuya-norain
  
Simple script and a docker image to turn on tuya sprinklers. Used with Holman WX2 - so hub supported.
Uses tuya-cli to control, openweatherapi to detect rain using some pretty average logic
  
## Docker-compose example
  
```
  tuya:
    image: tuya:latest
    container_name: tuya
    volumes:
      - /home/user/tuya:/tuya
    restart: always
    environment:
      - TZ=America/New_York
      - WEATHER_API_KEY=<openweatherapikey>
      - WEATHER_LAT=<lat>
      - WEATHER_LONG=<long>
      - WEATHER_CITY_ID=<cityid>
      - WEATHER_STORE=/tuya
      - WEATHER_DEBUG_MODE=False
      - WEATHER_RAIN_THRESHOLD=5
      - 'WEATHER_ROUTINE={"use_hub": true, "hub_id": "hubid", "hub_ip": "192.168.1.1", "hub_key": "hubkey", "shedules": [{"CID": "XXX", "id": 0, "delay": 1}]}'

```
  
## Build
  
```
docker build -t tuya .
# Deploy
docker tag tuya maxtara/tuya:latest
docker push maxtara/tuya
```

## Tuya Reference
  
```
DPS = {
    "101": 0,    # air temperature
    "102": 0,    # soil moisture
    "103": 4,    # amount of water used last time
    "105": "2",  # Battery level - 2=full, 1=half, 0=empty
    "106": "1",   # 1 when runs water, 0 when stopped, 3 when stoped and time/rain delay active
    "107": 4,     # minutes set for manual run, up to 60 (starts with 108)
    "108": False, # starts manual countdown when False
    "113": "48",  # delay to skip
    "114": "24",  # don"t know
    "115": False, # presence of soil sensor
    "116": False, # presence of rain sensor? (guess)
    "117": False,  # presence of TAP? (guess)
    "119": "1",   # 1 = litres/C 2 = Gal/F
    "120": 0,     # amount of rain? (guess)
    "125": False, # pause due to high soil moisture
    "127": "HOL9-018-023-000-000",
    "150": 0,
    "151": 0,
    "152": 7, # amount of water used last time
    "153": "1", # 1 when runs water, 0 when stopped, 3 when stopped and time/rain delay active
    "154": 5, # minutes set for manual run,
    "155": False, # starts manual countdown when False
    "160": "0",
    "161": False,
    "162": False,
    "166": False
},

```