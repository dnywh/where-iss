# Where ISS

![Where ISS Sequence.gif](https://res.cloudinary.com/dannywhite/image/upload/v1672986889/github/where-iss-sequence.gif)

Where ISS is a [Pi Frame](https://github.com/dnywh/pi-frame) app. It prints what the International Space Station sees of Earth to an e-ink/e-Paper display via Raspberry Pi.

Where ISS relies on the [Open Notify International Space Station Current Location API](http://open-notify.org/Open-Notify-API/ISS-Location-Now/) for tracking the whereabouts of the space station and the [Mapbox Raster Tiles API](https://docs.mapbox.com/api/overview/) for rendering subsequent map tiles.

## Prerequisites

To run Where ISS you need to first:

1. Join a Wi-Fi network on your Raspberry Pi
2. Enable SSH on your Raspberry Pi
3. Plug in a Waveshare e-Paper or similar display to your Raspberry Pi

Where ISS works great with [Pi Frame](https://github.com/dnywh/pi-frame), which includes the Waveshare drivers amongst other things like a scheduling template. If you’d prefer not to use Pi Frame, you’ll need to upload the [Waveshare e-Paper display drivers](https://github.com/waveshare/e-Paper/tree/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd) (or similar) to your Raspberry Pi in a _lib_ directory that is a sibling of Where ISS’. Here's an example:

```
.
└── where-iss
└── lib
    └── waveshare_epd
        ├── __init__.py
        ├── epdconfig.py
        └── epd5in83_V2.py
```

Either way, Waveshare displays require some additional setup. See the [Hardware Connection](https://www.waveshare.com/wiki/7.5inch_e-Paper_HAT_Manual#Hardware_Connection) and [Python](https://www.waveshare.com/wiki/7.5inch_e-Paper_HAT_Manual#Python) sections of your model’s manual.

## Get started

If you haven’t already, copy all the contents of this Where ISS repository over to the main directory of your Raspberry Pi.

### Set the display driver

Look for this line as the last import in _[app.py](https://github.com/dnywh/where-iss/blob/main/app.py)_:

```python
from waveshare_epd import epd5in83_V2 as display
```

Swap out the `epd5in83_V2` for your Waveshare e-Paper display driver, which should be in the _lib_ directory. Non-Waveshare displays should be imported here too, although you’ll need to make display-specific adjustments in the handful of places `display` is called further on.

### Install required packages

See _[requirements.txt](https://github.com/dnywh/where-iss/blob/main/requirements.txt)_ for a short list of required packages. Install each package on your Raspberry Pi using `sudo apt-get`. Here’s an example:

```bash
sudo apt-get update
sudo apt-get install python3-pil
sudo apt-get install python3-requests
```

### Enter your Mapbox credentials

Fill out an *env.py* file in the Where ISS directory with your [Mapbox access token](https://docs.mapbox.com/help/getting-started/access-tokens/). An example is provided in [_env.example.py_](https://github.com/dnywh/where-iss/blob/main/env.example.py).

### Run the app

Run Where ISS just like you would any other Python file on a Raspberry Pi:

```bash
cd where-iss
python3 app.py
```

Where ISS is noisy by default. Look for the results in Terminal.

---

## Usage

### Run on a schedule

See [Pi Frame](https://github.com/dnywh/pi-frame) for a crontab template and usage instructions.

### Design options

Where ISS contains several visual design parameters in _[app.py](https://github.com/dnywh/where-iss/blob/main/app.py)_.

| Option                    | Type    | Description                                                                                                                                         |
| ------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `minForegroundPercentage` | Integer | The minimum percentage for the foreground colour. A map tile with less than this will not be printed.                                               |
| `maxZoomLevel`            | Integer | The maximum (and starting) zoom level for the map tile.                                                                                             |
| `minZoomLevel`            | Integer | The minimum zoom level for the map tile. A map tile that doesn’t pass `minForegroundPercentage` rules and is at `minZoomLevel` will not be printed. |
| `invertZoomLevel`         | Integer | At what zoom level to invert the colours. Can make for better legibility of coastlines.                                                             |
| `contrast`                | Integer | A Pillow `.enhance` value for `ImageEnhance`.Contrast.                                                                                              |

### Save to folder

Where ISS contains an `exportImages` boolean option in _[app.py](https://github.com/dnywh/where-iss/blob/main/app.py)._ When `True` it saves both the original colour image, a processed image, and text file to a timestamped directory within an _exports_ directory.
