import RPi.GPIO as GPIO
import time
import requests
import json
import logging
from lcd_manager import write_message, write_temporary_message, set_main_menu_message
from enum import Enum
from typing import Type
from Freenove_DHT import DHT
from datetime import datetime, timedelta
from functools import lru_cache

# Pin Definitions
DHT_PIN = 29
RED_LED_PIN = 31
BLUE_LED_PIN = 15
GREEN_LED_PIN = 13
UP_BUTTON_PIN = 16
DOWN_BUTTON_PIN = 18
DOOR_BUTTON_PIN = 22

# Initial desired temperature
desired_temp = 75
weather_index = 0
current_weather_index = 0

# this is for calculating the bill                                                   
hvac_start_time = 0
hvac_end_time = 0

api_key = '1b89487e-3945-4c58-8545-94b9c35d6a26'

total_energy = 0
total_cost = 0

class HVAC_STATE(Enum):
    OFF = 0
    HEAT = 1
    COOL = 2
    IDLE = 3

class DOOR_STATE(Enum):
    CLOSED = 0
    OPEN = 1

CURRENT_DOOR_STATE = DOOR_STATE.CLOSED
PREV_HVAC_STATE = HVAC_STATE.IDLE
CURRENT_HVAC_STATE = HVAC_STATE.IDLE

# Setup GPIOs
GPIO.setmode(GPIO.BOARD)
GPIO.setup(RED_LED_PIN, GPIO.OUT)
GPIO.setup(BLUE_LED_PIN, GPIO.OUT)
GPIO.setup(UP_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DOWN_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DOOR_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DHT_PIN, GPIO.IN)
dht = DHT(DHT_PIN)

@lru_cache(maxsize=24)
def get_humidity_from_CIMIS(app_key=api_key, targets='75', start_date='2010-06-01', end_date='2010-06-01') -> int:
    # TODO: implement function to retrieve humidity data from CIMIS system
    base_url = 'http://et.water.ca.gov/api/data'
    params = {
        'appKey': app_key,
        'targets': targets,
        'startDate': start_date,
        'endDate': end_date
    }

    response = requests.get(base_url, params=params)
    data = None
    # Check if the request was successful
    if response.status_code == 200:
        try:
            data = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            logging.error("Failed to decode JSON from response")
            return None
        providers = data.get('Data', {}).get('Providers', [])
        day_rel_hum_avg_values = []

        for provider in providers:
            records = provider.get('Records', [])
            for record in records:
                # Get the 'DayRelHumAvg' value
                day_rel_hum_avg = record.get('DayRelHumAvg', {}).get('Value')
                if day_rel_hum_avg is not None:
                    day_rel_hum_avg_values.append(day_rel_hum_avg)
        return int(day_rel_hum_avg_values[0])

    else:
        logging.error(f"Request failed with status code {response.status_code}")
        return None

def door_action(channel):
    global CURRENT_DOOR_STATE
    if CURRENT_DOOR_STATE == DOOR_STATE.CLOSED:
        CURRENT_DOOR_STATE = DOOR_STATE.OPEN
        set_main_menu_message('OPEN', 'door')
        write_temporary_message("Door is open", duration=3)
        print('Door is open')
        logging.info('Door is open')
        time.sleep(2)
        turn_off_hvac()
        return
    else:
        CURRENT_DOOR_STATE = DOOR_STATE.CLOSED
        set_main_menu_message('SAFE', 'door')
        write_temporary_message("Door is closed", duration=3)
        print('Door is closed')
        logging.info('Door is closed')
        


def adjust_desired_temp(channel):
    global desired_temp, weather_index
    print('Button is pressed')
    if channel == UP_BUTTON_PIN:
        desired_temp = min(95, desired_temp + 1)
        print('desired temp is now ' + str(desired_temp))
        message = str(weather_index) + '/' + str(desired_temp)
        set_main_menu_message(message, 'temp')
        write_temporary_message("Adjusted Temp:" + str(desired_temp), duration=3) 
    else:
        desired_temp = max(65, desired_temp - 1)
        print('desired temp is now ' + str(desired_temp))
        message = str(weather_index) + '/' + str(desired_temp)
        set_main_menu_message(message, 'temp')
        write_temporary_message("Adjusted Temp:" + str(desired_temp), duration=3)

def calculate_weather_index(temperature, humidity) -> int:
    temperature = temperature * 9 / 5 + 32
    return round(temperature + 0.05 * humidity)

def turn_on_AC():
    global hvac_start_time
    hvac_start_time = time.time()
    GPIO.output(BLUE_LED_PIN, GPIO.HIGH)
    GPIO.output(RED_LED_PIN, GPIO.LOW)
    logging.info("AC is on")
    set_main_menu_message('AC', 'hvac')
    write_temporary_message("AC is on", duration=3)
    time.sleep(1.5)

def turn_on_heater():
    global hvac_start_time
    hvac_start_time = time.time()
    GPIO.output(RED_LED_PIN, GPIO.HIGH)
    GPIO.output(BLUE_LED_PIN, GPIO.LOW)
    logging.info("Heater is on")
    set_main_menu_message('HEAT', 'hvac')
    write_temporary_message("Heater is on", duration=3)
    time.sleep(1.5)

def turn_off_hvac():
    global hvac_start_time
    hvac_start_time = time.time()
    GPIO.output(RED_LED_PIN, GPIO.LOW)
    GPIO.output(BLUE_LED_PIN, GPIO.LOW)
    logging.info("HVAC is off")
    set_main_menu_message('OFF', 'hvac')
    write_temporary_message("HVAC is off", duration=3)
    time.sleep(1.5)

def control_hvac(temperature)-> Type[HVAC_STATE]:
    global current_weather_index, weather_index, desired_temp, CURRENT_DOOR_STATE, CURRENT_HVAC_STATE
    # print current hvac state 
    print(f"Current HVAC state: {CURRENT_HVAC_STATE}")
    # format date for CIMIS API query parameters
    now = datetime.now() - timedelta(days=2)
    formatted_date = now.strftime('%Y-%m-%d')
    # get humidity from CIMIS, loop until return value is not None since CIMIS API is unreliable
    humidity = None
    while humidity is None:
        humidity = get_humidity_from_CIMIS(targets='75', start_date=formatted_date, end_date=formatted_date)
    print(f"Current humidity: {humidity}")
    weather_index = calculate_weather_index(temperature, humidity) 
    if current_weather_index != weather_index:
        current_weather_index = weather_index
        set_main_menu_message(str(weather_index) + '/' + str(desired_temp), 'temp')
        write_temporary_message("New WI:" + str(weather_index), duration=1.5)
    print(f"Current weather index: {weather_index}")
    if 95 < weather_index: # fire alarm system is on
        write_message("Fire! HVAC OFF" + '\n' + 'Door/Window OPEN')
        logging.info('Fire alarm is started')
        CURRENT_DOOR_STATE = DOOR_STATE.OPEN
        while(calculate_weather_index(round(read_temperture()), humidity) > 95):
            flash_leds() 
        logging.info('Fire alarm is stopped')
        set_main_menu_message('', '')
        set_main_menu_message('SAFE', 'door')
        set_main_menu_message('COOL', 'hvac')
        write_temporary_message("Door is closed", duration=3)
        time.sleep(2)
        CURRENT_DOOR_STATE = DOOR_STATE.CLOSED
        turn_on_AC()
        return HVAC_STATE.COOL
    elif CURRENT_DOOR_STATE == DOOR_STATE.OPEN:
        # turn off HVAC
        return HVAC_STATE.OFF
    elif weather_index > desired_temp + 3:
        # turn on AC
        if CURRENT_HVAC_STATE != HVAC_STATE.COOL:
            turn_on_AC()
        return HVAC_STATE.COOL
    elif weather_index < desired_temp - 3:
        # turn on heater
        if CURRENT_HVAC_STATE != HVAC_STATE.HEAT:
            turn_on_heater()
        return HVAC_STATE.HEAT
    else:
        # turn off HVAC
        if CURRENT_HVAC_STATE != HVAC_STATE.OFF:
            turn_off_hvac()
        return HVAC_STATE.OFF 

def flash_leds():
# flash both LEDs for one second periodically
    GPIO.output(RED_LED_PIN, GPIO.HIGH)
    GPIO.output(BLUE_LED_PIN, GPIO.HIGH)
    GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(RED_LED_PIN, GPIO.LOW)
    GPIO.output(BLUE_LED_PIN, GPIO.LOW)
    GPIO.output(GREEN_LED_PIN, GPIO.LOW)
    time.sleep(1)


def read_temperture() -> float:
    for i in range(0, 5):
        chk = dht.readDHT11()
        if (chk is dht.DHTLIB_OK):
            return dht.temperature

# Initialization
def setup():
    GPIO.setwarnings(False)
    set_main_menu_message('SAFE', 'door')
    GPIO.add_event_detect(UP_BUTTON_PIN, GPIO.RISING, callback=adjust_desired_temp, bouncetime=200)
    GPIO.add_event_detect(DOWN_BUTTON_PIN, GPIO.RISING, callback=adjust_desired_temp, bouncetime=200)
    GPIO.add_event_detect(DOOR_BUTTON_PIN, GPIO.FALLING, callback=door_action, bouncetime=4000)

# Loop
def loop():
    global PREV_HVAC_STATE, CURRENT_HVAC_STATE, total_cost, total_energy
    temperature = round(read_temperture())
    CURRENT_HVAC_STATE = control_hvac(temperature)
    if CURRENT_HVAC_STATE != PREV_HVAC_STATE:
        hvac_end_time = time.time()
        if PREV_HVAC_STATE == HVAC_STATE.HEAT:
            total_energy += (hvac_end_time - hvac_start_time) / 100
            total_cost += total_energy * 0.5
            write_temporary_message(f'energy: {total_energy}KWh \ncost: ${total_cost}', duration=3)
        elif PREV_HVAC_STATE == HVAC_STATE.COOL:
            total_energy += (hvac_end_time - hvac_start_time) / 200
            total_cost = total_energy * 0.5
            write_temporary_message(f'energy: {total_energy}KWh \ncost: ${total_cost}', duration=3)
        elif PREV_HVAC_STATE == HVAC_STATE.OFF:
            write_temporary_message(f'energy: {total_energy}KWh \ncost: ${total_cost}', duration=3)
        PREV_HVAC_STATE = CURRENT_HVAC_STATE
    time.sleep(1.5)

# Cleanup
def cleanup():
    # clear all states
    GPIO.cleanup()
