import RPi.GPIO as GPIO
import time
import threading
import logging
from lcd_manager import write_message, write_temporary_message, set_main_menu_message

# Set pin mode
GPIO.setmode(GPIO.BOARD)

# Set up pins
PIR_PIN = 33
LED_PIN = 13

GPIO.setup(LED_PIN, GPIO.OUT)

timer = None

def turn_on_light():
    global timer
    if timer is not None:
        timer.cancel()
    else:
        logging.info('Turning on light')
        set_main_menu_message('ON', 'light')
        write_temporary_message("Light is on", duration=3)
    print("Motion detected!")
    GPIO.output(LED_PIN, GPIO.HIGH)
    timer = threading.Timer(10, turn_off_light)
    timer.start()

def turn_off_light():
    global timer
    GPIO.output(LED_PIN, GPIO.LOW)
    print("No motion detected")
    set_main_menu_message('OFF', 'light')
    write_temporary_message("Light is off", duration=3)
    logging.info('Turning off light')
    timer = None

# Initialization
def setup():
    time.sleep(2)
    logging.info('PIR is ready')
    GPIO.setup(PIR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.output(LED_PIN, GPIO.LOW)

# Loop
def loop():
    if GPIO.input(PIR_PIN):
        turn_on_light()
    else:
        turn_off_light()
    time.sleep(1)

# Cleanup
def cleanup():
    GPIO.cleanup()
