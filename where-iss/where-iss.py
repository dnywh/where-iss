import sys
import os
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)


import logging
from waveshare_epd import epd7in5_V2 # Waveshare display
# import time # Delays in seconds, not used, right? TODO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance # Image and graphics
# import traceback # TODO: Did removing this do anything? From Waveshare demo

import requests # Needed to check the ISS location
import secrets  # Needed for Mapbox access token
import math  # Needed for converting lat and long
import urllib.request # Needed for saving the Mapbox image
from datetime import datetime # For appending a timestamp on file images


mapboxAccessToken = secrets.MAPBOX_ACCESS_TOKEN

logging.basicConfig(level=logging.DEBUG)

# Enable/disable little info display at bottom of map
mapDebug = False

# Get API results
issData = requests.get("http://api.open-notify.org/iss-now.json").json()
issLat = float(issData['iss_position']['latitude'])
issLon = float(issData['iss_position']['longitude'])


# Converts from latitude and longtitude to Slippy Map tilenames
# https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Lon./lat._to_tile_numbers_2
def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)


mapTileZoom = 8 # 10: See fields, 8: See ridges
# Get tilenames
mapTileNameX = deg2num(issLat, issLon, mapTileZoom)[0]
mapTileNameY = deg2num(issLat, issLon, mapTileZoom)[1]
mapTileUrl = f"https://api.mapbox.com/v4/mapbox.satellite/{mapTileZoom}/{mapTileNameX}/{mapTileNameY}@2x.jpg90?access_token={mapboxAccessToken}"

# My Waveshare EDP is 7.5", 800x480
mapImageWidth = 400
# And I want the map tile to be a square in the center of that Square
mapImageHeight = mapImageWidth
mapTileSize = (mapImageWidth, mapImageHeight)

try:
    timeStampNice = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"Kicking this off at {timeStampNice} UTC")
    logging.info(f"ISS latitude: {issLat}, ISS longitude: {issLon}")
    logging.info(f"Map tile image: {mapTileUrl}")
    # Save a copy of the map tile
    urllib.request.urlretrieve(f"https://api.mapbox.com/v4/mapbox.satellite/{mapTileZoom}/{mapTileNameX}/{mapTileNameY}@2x.jpg90?access_token={mapboxAccessToken}", "map-tile.jpg")

    # Construct basic image
    mapImageColor = Image.open('map-tile.jpg')
    mapImageGrayscale = mapImageColor.convert('L')

    # Check to see if image is interesting enough to print to e-Paper...
    extrema = mapImageGrayscale.getextrema()
    pixelRange = extrema[1] - extrema[0]
    pixelRangeMinimum = 50 # 8
    
    # Pixel range should be larger than pixelRangeMinimum
    # Exit if not
    if pixelRange < pixelRangeMinimum:
        logging.info(f"Pixel range of {pixelRange} probably makes for an uninteresting image. Exiting early and keeping what's already on the e-Paper screen.")
        exit()
    else:
        logging.info(f"Pixel range of {pixelRange}. Let's print.")
    
    # Keep going...

    # Increase contrast on image
    enhancer = ImageEnhance.Contrast(mapImageGrayscale)
    mapImageGrayscaleBetterContrast = enhancer.enhance(2) # 1 = no changes, 1.5 = modest
    # mapImageDithered = mapImageGrayscale.convert('1', dither=Image.NONE)
    # Resize image
    mapImageEndResult = mapImageGrayscaleBetterContrast.resize(mapTileSize)
    # Save out image
    timeStampSlug = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
    fullImageUrl = f'{picdir}/map-tile-{timeStampSlug}.jpg'
    mapImageEndResult.save(fullImageUrl) # Save the image to the appropriate folder
    logging.info(f"Image saved to: {fullImageUrl}")

    # Begin rendering
    epd = epd7in5_V2.EPD()
    epd.init()
    epd.Clear()
    
    font12 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 12)

    # Create image (I'm calling it canvas) on the landscape plane
    # https://pillow.readthedocs.io/en/stable/reference/Image.html#constructing-images
    canvas = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame
    # Get a drawing context
    draw = ImageDraw.Draw(canvas) 

    # Place map image in center of canvas
    mapImageX = int((epd.width - mapImageWidth) / 2)
    mapImageY = int((epd.height - mapImageHeight) / 2)
    canvas.paste(mapImageEndResult, (mapImageX, mapImageY))

    if mapDebug:
        # Draw debugging text inside a rectangle that's at the bottom of map image
        infoRectHeight = 96
        infoRectY = mapImageY + mapImageHeight - infoRectHeight
        draw.rectangle(((mapImageX, infoRectY), (mapImageX + mapImageWidth, mapImageY + mapImageHeight)), fill=1)
        infoTextX = 44
        infoTextY = 12
        draw.text((mapImageX + infoTextX, infoRectY + infoTextY), f"Map Zoom: {mapTileZoom}", font=font12, fill=0)
        draw.multiline_text((mapImageX + infoTextX, infoRectY + infoTextY + 22), f"Latitude: {issLat}\nLongitude: {issLon}", font=font12, fill=0)

    # Render all of the above to the e-Paper
    epd.display(epd.getbuffer(canvas))


    # Clear screen (commented out so it can stay on)
    # logging.info("Putting display to sleep")
    # time.sleep(12) # Delay
    # epd.init()
    # epd.Clear()
    # epd.sleep()

    # Put e-Paper on pause, keeping what's on screen
    epd.sleep()

except IOError as e:
    logging.info(e)

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    epd7in5_V2.epdconfig.module_exit()
    exit()
