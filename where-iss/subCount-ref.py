#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import requests
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from waveshare_epd import epd7in5b_HD
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

from datetime import date
today = str(date.today())

logging.basicConfig(level=logging.DEBUG)

# Set up the structure of the API request URL

URL = "https://www.googleapis.com/youtube/v3/channels"
type = "statistics"
channelid = "******"
apikey = "******"
PARAMS = {('part', type), ('id',channelid), ('key',apikey)}

#Get API results

r = requests.get(url = URL, params = PARAMS)
data = r.json()
subscribers = int(data['items'][0]['statistics']['subscriberCount'])
totalviews = int(data['items'][0]['statistics']['viewCount'])

#Convert results to a string and format numbers with commas

noViews = 'Views:   ' + f"{totalviews:,d}"
noSubs = 'Subscribers:   ' + f"{subscribers:,d}"

#Update the display

try:
    logging.info("Updating display")

    epd = epd7in5b_HD.EPD()
    logging.info("initialising and clearing display")
    epd.init()
    epd.Clear()

    font12 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 12)
    font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
    font32 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 32)

    logging.info("Drawing new image")
    blackImage = Image.new('1', (epd.width, epd.height), 255)
    redImage = Image.new('1', (epd.width, epd.height), 255)
    draw_blackImage = ImageDraw.Draw(blackImage)
    draw_redImage = ImageDraw.Draw(redImage)
    draw_blackImage.text((312, 360), 'Michael Klements', font = font32, fill = 0)
    draw_blackImage.text((200, 435), noViews, font = font24, fill = 0)
    draw_blackImage.text((475, 435), noSubs, font = font24, fill = 0)
    draw_blackImage.text((800, 500), today, font = font12, fill = 0)
    bmp = Image.open(os.path.join(picdir, 'youtubeIcon.bmp'))
    redImage.paste(bmp, (265,80))
    epd.display(epd.getbuffer(blackImage),epd.getbuffer(redImage))
    
    #To delay before clearing, if used
    
    #time.sleep(20)

    #To clear the display afterwards
    
    #logging.info("Clear...")
    #epd.init()
    #epd.Clear()

    logging.info("Putting display to sleep")
    epd.sleep()
    epd.Dev_exit()
    
except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    epd7in5b_HD.epdconfig.module_exit()
    exit()

