# Where ISS

Use your Pi and Waveshare ePaper/e-ink display to track the International Space Station's (ISS) whereabouts.

This was a long journey for me so I've split the repo up into steps for anyone in a similar situation.

- Copy your own Waveshare driver .py file into the lib/waveshare*epd directory. I've used the 7.5" version, hence \_epd7in5_V2.py*.
  - Make appropriate edits at bottom of file. See mine
- Set a CRON job (see cron.example) use crontab guru
  - Make timezone UTC (`sudo raspi-config` > Localisation Options > Timezone > None of the above > UTC)
  - Check via `date`

---

## Setup

```
sudo pip3 install spidev # From Waveshare wiki
# etc
sudo pip3 install global-land-mask

```

## Files in more detail

<!-- ### Hello World

Using the Waveshare file to make sure everything works as expected.

### Hello Internet

Talk to the space station. Use secrets.py

### Hello Design

Get fonts and images working. -->

---

## Internet

For all of these (excluding _Hello World_), you need your Wi-Fi credentials. See _secrets.example.py_ for that.

1. Change _secrets.example.py_ to _secrets.py_
2. Fill in your credentials

## Ideas

### Check to see if coordinates are over land or water

...and don't bother rendering if over water.

```py
# Imports for checking if ISS is over land or water
# https://github.com/toddkarin/global-land-mask
from global_land_mask import globe
import numpy as np
```

No dice as my Pi Zero W doesn't have enough RAM. So my alternative is using PIL's `getextrema()` to see how much variance there is in the image's pixel values.
