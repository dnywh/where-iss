# Where ISS?

Track the International Space Station's (ISS) orbit by printing what they see of Earth to an e-ink display.

Designed for Raspberry Pi and Waveshare e-Paper display HAT. Likely work on any display with a decent resolution after some minor tweaks.

---

This was a long journey for me so I've split the repo up into steps for anyone in a similar situation.

- Copy your own Waveshare driver .py file into the lib/waveshare*epd directory. I've used the 7.5" version, hence \_epd7in5_V2.py*.
  - Make appropriate edits at bottom of file. See mine
- Set a CRON job (see cron.example) use crontab guru
  - Make timezone UTC (`sudo raspi-config` > Localisation Options > Timezone > None of the above > UTC)
  - Check via `date`

---

## Setup

### Code formatting

_autopep8_ seems to break the code by rearranging imports. _black_ works for me.
