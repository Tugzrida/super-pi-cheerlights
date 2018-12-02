#!/usr/bin/python

# super-pi-cheerlights: getsun.py: runs daily to save sunset times to sunset.json
# Copyright (C) 2018 Tugzrida (github.com/Tugzrida)
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This script is designed to run every day and updates
# sunset.json with new sunset times from the sunrise-sunset.org
# API. Take note that if this script is run while the
# lights are on, but after midnight, the lights will
# switch off as sunset.json will be updated for the new
# day. The main file will only run this script automatically
# after the lights have gone off for the night, however running
# this script directly or using the web UI will work at any time.

from os import path
from json import dumps
from dateutil.parser import parse
from datetime import date, datetime, timedelta
from requests import get
from requests.exceptions import ConnectionError
from pytz import timezone

###################################
# Settings specific to each setup #
###################################
# See further settings in super-pi-cheerlights.py(Builtin server, white balance and colour definitions) and www/index.html(display led tape and/or fairy lights controls)

# Location - Used for local sunset times - can be found using https://www.gps-coordinates.net/
lat = "0.0"
lon = "0.0"

# Timezone - All timezones can be listed with list_tz.py
timeZone = "UTC"

# Chronologinal Order of Events:
# Sunset:                LED Tape begins to fade up
# End of Civil Twilight: LED Tape is fully lit, fairy lights turn on
# Off time:              LED Tape fades out and fairy lights turn off

# Off time:
offhour = 22 # Hour, in 24 hour time
offmin = 0   # Minute
offsec = 0   # Second
offday = 0   # 0 if off time is before midnight, 1 if at or after midnight

# Manual start: If you don't want the system to start by the sun times, 
# or if you live too far North or South (past ~60deg) to have a defined sunset.
manualstart = False # False for automatic sunset times, True for manual times

# Manually set "sunset" time. See "Order of Events" above for details.
mansunsethour = 19 # Hour, in 24 hour time
mansunsetmin = 0  # Minute
mansunsetsec = 0   # Second
mansunsetday = 0   # 0 if before midnight, 1 if at or after midnight

# Manually set "end of civil twilight" time. See "Order of Events" above for details.
mantwilighthour = 19 # Hour, in 24 hour time
mantwilightmin = 30  # Minute
mantwilightsec = 0   # Second
mantwilightday = 0   # 0 if before midnight, 1 if at or after midnight
###################################

try:
    if not manualstart:
        # load times from API
        now = datetime.now(timezone(timeZone))
        sun = get("https://api.sunrise-sunset.org/json?lat=%s&lng=%s&formatted=0&date=%s-%s-%s" % (lat, lon, now.year, now.month, now.day)).json()
        sunset = parse(sun["results"]["sunset"]).astimezone(timezone(timeZone)) # sunset time, earlier than twilight
        twilight = parse(sun["results"]["civil_twilight_end"]).astimezone(timezone(timeZone)) # end of civil twilight, sun is more than 6deg below horizon, later than sunset
    else:
        sunset = datetime.now(timezone(timeZone)).replace(hour=mansunsethour, minute=mansunsetmin, second=mansunsetsec, microsecond=0) + timedelta(days=mansunsetday) # manual sunset time, change above
        twilight = datetime.now(timezone(timeZone)).replace(hour=mantwilighthour, minute=mantwilightmin, second=mantwilightsec, microsecond=0) + timedelta(days=mantwilightday) # manual end of civil twilight time, change above
    
    off = datetime.now(timezone(timeZone)).replace(hour=offhour, minute=offmin, second=offsec, microsecond=0) + timedelta(days=offday) # time for lights to turn off, change above
    twilightdur = twilight - sunset # time from sunset - end of civil twilight
    
    # save to file
    f = open(path.join(path.dirname(path.abspath(__file__)), 'sunset.json'), 'w')
    f.write(dumps({"sunset": sunset.isoformat(), "twilight": twilight.isoformat(), "twilightdur": twilightdur.seconds, "off": off.isoformat(), "timezone": timeZone}))
    f.close()
except ConnectionError:
    print('Connection error. Leaving sunset.json as is.')
