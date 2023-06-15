from PCF8574 import PCF8574_GPIO
from Adafruit_LCD1602 import Adafruit_CharLCD
import RPi.GPIO as GPIO
import threading
import time

# Setting up LCD Display (Freenova website)
PCF8574_address = 0x27
PCF8574A_address = 0x3F

try: 
    mcp = PCF8574_GPIO(PCF8574_address)
except: 
    try: 
        mcp = PCF8574_GPIO(PCF8574A_address)
    except: 
        print('I2C Address Error !')
        exit(1)

lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)

current_message = None
main_menu_message_dict = {'temp': '', 'door': '', 'hvac': '', 'light': ''}
main_menu_message = 'main menu'
message_lock = threading.Lock()

def write_message(message, temporary=False):
    global current_message

    if not temporary:
        current_message = message

    lcd.clear()
    lcd.message(message)

def write_temporary_message(message, duration=3):
    with message_lock:
        write_message(message, temporary=True)
    threading.Timer(duration, restore_message).start()


def restore_message():
    print('restoring message')
    global current_message, main_menu_message
    with message_lock:
        if current_message is not None:
            print('restoring message to: ' + current_message)
            write_message(current_message)
        else:
            print('Restoring message to: ' + main_menu_message)
            write_message(main_menu_message, temporary=True)

def set_main_menu_message(message, param):
    global main_menu_message
    global main_menu_message_dict
    global current_message
    # accounts for the case of resetting the main menu message to blank
    if message == '' and param == '':
        main_menu_message_dict = {'temp': '', 'door': '', 'hvac': '', 'light': ''}
        current_message = None
    else:
        main_menu_message_dict[param] = message
    main_menu_message = _convert_dict_to_string(main_menu_message_dict)
    print(main_menu_message)


def _convert_dict_to_string(message_dict):
    message = ''
    message  = message + 'T:' + message_dict['temp']  + '  '
    message  = message + 'D:' + message_dict['door']  + '    ' + '\n'
    message  = message + 'H:' + message_dict['hvac']  + '    '
    message  = message + 'L:' + message_dict['light']  + '    '
    return message

def setup():
    mcp.output(3,1)     # turn on LCD backlight
    lcd.begin(16,2)
    lcd.setCursor(0,0)

def cleanup():
    lcd.clear()
    lcd.setCursor(0,0)
    GPIO.cleanup()


