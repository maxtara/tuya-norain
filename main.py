import urllib.request
import os
import json
import datetime
import subprocess
import argparse
import time
import os
import glob
import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

APIKEY = os.environ["WEATHER_API_KEY"]
LAT = os.environ["WEATHER_LAT"]
CITY_ID = os.environ["WEATHER_CITY_ID"]
LONG = os.environ["WEATHER_LONG"]
DEBUG = os.environ.get("WEATHER_DEBUG_MODE", "False") == "True"
DATASTORE = os.environ["WEATHER_STORE"]
NOW = datetime.datetime.now()
RAIN_THRESHOLD = int(os.environ.get("WEATHER_RAIN_THRESHOLD", "5"))
routine_dummy = {
    "use_hub": True,
    "hub_id": "hubid",
    "hub_ip": "192.168.1.1",
    "hub_key": "hubkey",
    "shedules": [{"CID": "cid1", "id": 0, "delay": 2}, {"CID": "cid2", "id": 1, "delay": 2}, {"CID": "cid3", "id": 0, "delay": 4}, {"CID": "cid4", "id": 1, "delay": 4}],
}
ROUTINE = os.environ.get("WEATHER_ROUTINE", json.dumps(routine_dummy))
ROUTINE = json.loads(ROUTINE)


def delete_very_old_data():
    old = NOW - datetime.timedelta(days=65)
    filename = datetime.datetime.strftime(old, "%Y%m") + "*.json"
    globs = os.path.join(DATASTORE, filename)
    subprocess.call(["rm", globs])


def store_weather():
    weather_now_url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LONG}&appid={APIKEY}"
    contents_raw = urllib.request.urlopen(weather_now_url).read()
    contents = json.loads(contents_raw)
    filename = datetime.datetime.strftime(NOW, "%Y%m%d_%H") + ".json"
    path = os.path.join(DATASTORE, filename)
    json.dump(contents, open(path, "w"))
    delete_very_old_data()


def run_routine(routine):
    schedules = routine["shedules"]
    battery_alerted = False
    for schedule in schedules:
        sleep_seconds = schedule["delay"] * 60  # Config in mins
        logging.info(f"Running, then sleeping for {sleep_seconds} seconds")
        if routine.get("use_hub", False):
            start_sprinkler(schedule["CID"], routine["hub_ip"], routine["hub_id"], routine["hub_key"])
            battery_alerted = alert_battery(schedule["CID"], routine["hub_ip"], routine["hub_id"], routine["hub_key"], battery_alerted)
            time.sleep(sleep_seconds)
        else:
            start_sprinkler(None, schedule["ip"], schedule["id"], schedule["key"])
            battery_alerted = alert_battery(None, schedule["ip"], schedule["id"], schedule["key"], battery_alerted)
            time.sleep(sleep_seconds)


def get_rain(obj):
    """get_rain - Sometimes 1h, sometimes 3h.
    Not sure if this will double count or not.
    :param obj: list.rain from openweatherapi
    :return: mm of rain over the hour
    """
    if "1h" in obj:
        return obj["1h"]
    if "3h" in obj:
        return obj["3h"] / 3
    return 0.0


def get_past_rain_sum():
    filename = datetime.datetime.strftime(NOW, "%Y%m%d") + "*.json"
    files_glob = os.path.join(DATASTORE, filename)
    one_hour_sum = 0.0
    with_rain_count = 0
    logging.info(f"Summing data in this glob: {glob.glob(files_glob)}")
    for file in glob.glob(files_glob):
        hour_data = json.load(open(file))
        if "rain" in hour_data:
            with_rain_count += 1
            one_hour_sum += get_rain(hour_data["rain"])
    logging.info(f"Past found rain {with_rain_count} times, total being {one_hour_sum}")
    return one_hour_sum


def get_future_rain_sum():
    logging.info("Getting forecasted weather")
    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?id={CITY_ID}&appid={APIKEY}&cnt=12"
    contents_raw = urllib.request.urlopen(forecast_url).read()
    contents = json.loads(contents_raw)
    one_hour_sum = 0.0
    with_rain_count = 0
    for hour_data in contents["list"]:
        if "rain" in hour_data:
            with_rain_count += 1
            one_hour_sum += get_rain(hour_data["rain"])
    logging.info(f"Forcast found rain {with_rain_count} times, total being {one_hour_sum}")
    return one_hour_sum


def too_wet_for_routine():
    rain_total = get_past_rain_sum() + get_future_rain_sum()
    return rain_total > RAIN_THRESHOLD


def start_sprinkler(cid, num, ip, id, key):
    os.environ["DEBUG"] = "*"
    dps = "108" if num == 0 else "155"
    args = ["tuya-cli", "set", "--ip", ip, "--id", id, "--key", key, "--dps", dps, "--set", "false", "--protocol-version", "3.3"]  # False is start
    if cid:
        args += ["--cid", cid]

    if DEBUG:
        logging.info(f"Not actually Running {args}")
    else:
        logging.info(f"Running {args}")
        subprocess.call(args)


def is_battery_empty(cid, ip, id, key):
    os.environ["DEBUG"] = "*"
    args = ["tuya-cli", "get", "--ip", ip, "--id", id, "--key", key, "--dps", "105", "--protocol-version", "3.3"]  # False is start
    if cid:
        args += ["--cid", cid]
    if DEBUG:
        logging.info(f"Not actually Running {args}")
    else:
        logging.info(f"Running {args}")
        result = subprocess.check_output(args).strip()  # Returns b'2\n'
        return int(result)  # Convert bytes to int
    return 2


def alert_battery(cid, ip, id, key, previous_alert):
    level = is_battery_empty(cid, ip, id, key)
    if level == 0:
        logging.warning(f"Battery is low {level}) for device {cid}")
        if not previous_alert:
            previous_alert = True
            logging.error(f"ALERT - Battery is low {level}) for device {cid}")
    elif level == 1:
        logging.warning(f"Battery is medium {level}) for device {cid}")
    elif level == 2:
        logging.warning(f"Battery is full ({level}) for device {cid}")
    else:
        raise Exception(f"Unexpected battery level of {level}")
    return previous_alert


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--weatheronly", help="Just store weather", action="store_true")
    opts = argparser.parse_args()
    if opts.weatheronly:
        logging.info("Storing weather")
        store_weather()
        logging.info("Weather stored")
    else:
        logging.info("Running Routine")
        if not too_wet_for_routine():
            run_routine(ROUTINE)
            logging.info("Routine Ran")
        else:
            logging.info("Not running Routine")
