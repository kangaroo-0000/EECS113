from ambient_light import setup as ambient_light_setup, loop as ambient_light_loop, cleanup as ambient_light_cleanup
from hvac import setup as hvac_setup, loop as hvac_loop, cleanup as hvac_cleanup
from lcd_manager import setup as lcd_setup, cleanup as lcd_cleanup, write_message, write_temporary_message, set_main_menu_message
import RPi.GPIO as GPIO
import logging

def main():
    logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
    logging.info('Starting application')
    lcd_setup()
    hvac_setup()
    ambient_light_setup()
    
    while True:
        try:
            hvac_loop()
            ambient_light_loop()
        except KeyboardInterrupt:
            break

    hvac_cleanup()
    ambient_light_cleanup()
    lcd_cleanup()


if __name__ == "__main__":
    main()