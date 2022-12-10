# Imports
import sys
import os

exportsdir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "exports"
)
libdir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "lib"
)
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging  # Write to console
from waveshare_epd import epd7in5_V2  # Waveshare display
from PIL import Image, ImageEnhance, ImageOps  # Image and graphics
import requests  # To check the ISS location
import urllib.request  # For saving the Mapbox image
import secrets  # For Mapbox access token
import math  # For converting lat and long
from datetime import datetime  # For appending a timestamp on file images

# Settings
logging.basicConfig(level=logging.DEBUG)
# Required settings
mapboxAccessToken = secrets.MAPBOX_ACCESS_TOKEN
mapImageWidth = 360  # My Waveshare EDP is 7.5", 800x480, and I want the map image to be a bit smaller
mapImageHeight = 360  # And I want the map image to be square since the tiles are square
mapTileSize = (mapImageWidth, mapImageHeight)
# Optional settings
imageXOffset = 0
imageYOffset = 12  # Nudge down to match placement in picture frame
# Useful as ISS spends a lot of time over oceans, which looks boring on e-Paper
# pixelRangeMinimum = 128  # Anything lower than 128 is probably ocean. Images with even a smidge of land tend to be around 200+
minForegroundPercentage = 18  # Anything lower than 18% is probably uninteresting
# Set zoom range
# 2: whole continents, 4: recognisable contours, 8: ridges, 10: individual crops
minZoomLevel = 4
maxZoomLevel = 10
contrast = 2  # 1 = no changes, 1.5 = modest, 2 = noticeable, 3 = extreme

# Functions
# Converts from latitude and longtitude to the Slippy Map tilenames Mapbox wants
def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0**zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)  # Store x and y in tuple


# The main map printing function
def attemptMapPrint(mapTileZoom):
    # Use those ISS coordinates to find corresponding tilenames
    mapTileNameX = deg2num(issLat, issLon, mapTileZoom)[0]
    mapTileNameY = deg2num(issLat, issLon, mapTileZoom)[1]
    # Retreive a Mapbox tile image
    mapTileUrl = f"https://api.mapbox.com/v4/mapbox.satellite/{mapTileZoom}/{mapTileNameX}/{mapTileNameY}@2x.jpg90?access_token={mapboxAccessToken}"
    logging.info(f"Tile URL: {mapTileUrl}")

    # Prepare directory for saving image(s)
    timeStampSlugToMin = datetime.today().strftime("%Y-%m-%d-%H-%M")
    # timeStampSlugToSec = datetime.today().strftime("%Y-%m-%d-%H-%M-%S")
    imageDir = os.path.join(exportsdir, timeStampSlugToMin)
    if not os.path.exists(imageDir):
        os.mkdir(imageDir)

    # Download a temporary copy of the map tile to render to screen. Store it locally
    urllib.request.urlretrieve(
        f"https://api.mapbox.com/v4/mapbox.satellite/{mapTileZoom}/{mapTileNameX}/{mapTileNameY}@2x.jpg90?access_token={mapboxAccessToken}",
        "map-tile.jpg",
    )

    # Prepare versions of image
    mapImageColor = Image.open("map-tile.jpg")
    mapImageGrayscale = mapImageColor.convert("L")
    # Including a dithered version to mimick e-Paper screen for subsequent histogram math
    mapImageDithered = mapImageColor.convert("1")
    # Include versions with increased contrast for testing
    mapImageGrayscaleSharp = ImageEnhance.Contrast(mapImageGrayscale).enhance(contrast)
    mapImageDitheredSharp = mapImageGrayscaleSharp.convert("1")

    # Get information about image to see if it is interesting enough to print to e-Paper...
    extrema = mapImageGrayscale.getextrema()
    pixelRange = extrema[1] - extrema[0]
    histogram = mapImageDithered.histogram()
    backgroundPercentage = int(round(histogram[0] / (512 * 512), 2) * 100)
    foregroundPercentage = int(round(histogram[255] / (512 * 512), 2) * 100)
    logging.info(
        f"Foreground: {foregroundPercentage}%, Background: {backgroundPercentage}%. Pixel Range: {pixelRange}"
    )

    # Invert colors if ocean is visible so that ocean is white and land black
    if currentZoomLevel <= 5:
        mapImageInverted = ImageOps.invert(mapImageGrayscale)
        mapImageResult = mapImageInverted
    else:
        mapImageResult = mapImageGrayscale

    # Quality control
    # Check if histogram range is less than minimum
    if foregroundPercentage <= minForegroundPercentage:
        # Does not pass quality control
        # Create a rejects subdirectory if it doesn't already exist
        rejectsSubDir = os.path.join(imageDir, "rejects")
        if not os.path.exists(rejectsSubDir):
            os.mkdir(rejectsSubDir)
        # Save out image with zoom level in name (to two decimal places)
        rejectImageUrl = (
            f"{rejectsSubDir}/{timeStampSlugToMin}-zoom-{currentZoomLevel:02}.jpg"
        )
        mapImageResult.save(rejectImageUrl)
        # Return and try again
        logging.info(
            f"I think this might be an uninteresting image. Zooming out and trying again..."
        )
        return
    else:
        # Passed quality control
        logging.info(f"Looks good! Let's print.")
        # Continue

    # Save out image in its directory
    mapImageDithered.save(f"{imageDir}/{timeStampSlugToMin}-dithered.jpg")
    # Also save other variants for comparison
    mapImageColor.save(f"{imageDir}/{timeStampSlugToMin}-color.jpg")
    mapImageGrayscale.save(f"{imageDir}/{timeStampSlugToMin}-grayscale.jpg")
    mapImageDitheredSharp.save(f"{imageDir}/{timeStampSlugToMin}-dithered-sharp.jpg")
    mapImageGrayscaleSharp.save(f"{imageDir}/{timeStampSlugToMin}-grayscale-sharp.jpg")

    # Log information to text file
    output = f"Printed at:\t{timeStampNice}\nCoordinates:\t{issLat}, {issLon}\nMap zoom:\t{mapTileZoom}\nTile name:\t{mapTileNameX}, {mapTileNameY}\nForeground:\t{foregroundPercentage}%\nBackground:\t{backgroundPercentage}%\nPixel range:\t{pixelRange}\nTile URL:\t{mapTileUrl}"

    with open(f"{imageDir}/{timeStampSlugToMin}.txt", "w") as f:
        f.write(output)
    # Log same information to console
    logging.info(f"\n{output}")

    # Resize image
    mapImagePrinted = mapImageResult.resize(mapTileSize)

    # Begin rendering
    epd = epd7in5_V2.EPD()
    epd.init()
    epd.Clear()

    # Create canvas (called 'image' in Pillow docs) on the landscape plane
    canvas = Image.new("1", (epd.width, epd.height), 255)  # 255: clear the frame

    # Place map image in center of canvas
    mapImageX = int(imageXOffset + (epd.width - mapImageWidth) / 2)
    mapImageY = int(imageYOffset + (epd.height - mapImageHeight) / 2)
    canvas.paste(mapImagePrinted, (mapImageX, mapImageY))

    # Render all of the above to the e-Paper
    epd.display(epd.getbuffer(canvas))

    # Put e-Paper on pause, keeping what's on screen
    logging.info(f"Going to sleep. See you next time.")
    # See sleep.py for wiping the screen clean
    epd.sleep()

    # Exit application
    exit()


# Kick things off
try:
    timeStampNice = datetime.today().strftime("%Y-%m-%d %H:%M:%S UTC")
    logging.info(f"Kicking off at {timeStampNice}")
    # Get ISS latitude and longitude results
    issData = requests.get("http://api.open-notify.org/iss-now.json").json()
    issLat = float(issData["iss_position"]["latitude"])
    issLon = float(issData["iss_position"]["longitude"])
    logging.info(f"Coordinates: {issLat}, {issLon}")

    # Start at max zoom level before zooming out
    currentZoomLevel = maxZoomLevel
    # Decrement through map zoom levels until one is worth printing
    while True:
        logging.info(f"Map zoom: {currentZoomLevel}")
        # Unless the map zoom level has made all attempts within the range...
        # Map zoom level within range. Try to print
        attemptMapPrint(currentZoomLevel)
        # Didn't work? go down a zoom level for next time
        currentZoomLevel -= 1
        # Exit if map printed or couldn't produce desired contrast even at map zoom level 3
        if currentZoomLevel < minZoomLevel:
            logging.info(
                "I still couldn't get a good map image at these coordinates despite being fully zoomed out. Keeping what's on screen and going to sleep."
            )
            break


except IOError as e:
    logging.info(e)

# Exit plan
except KeyboardInterrupt:
    logging.info("^C:")
    epd7in5_V2.epdconfig.module_exit()
    exit()
