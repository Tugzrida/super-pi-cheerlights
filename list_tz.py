#!/usr/bin/python
# This file simply lists all of Pytz's timezones for reference when setting up
from pytz import all_timezones
for tz in all_timezones:
    print tz
