# Clears the Waveshare display and puts it properly to rest
# I run this on a CRON job so the screen gets a rest overnight

import sys
import os
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from waveshare_epd import epd7in5_V2

logging.basicConfig(level=logging.DEBUG)

try:
    epd = epd7in5_V2.EPD()
    
    logging.info("Wiping clean...")
    epd.init()
    epd.Clear()

    logging.info("Going to sleep. Good night.")
    epd.sleep()
    
except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    epd7in5_V2.epdconfig.module_exit()
    exit()
