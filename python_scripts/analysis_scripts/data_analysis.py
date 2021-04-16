import sys
sys.path.append('../')
import pandas as pd
from constants import *
from helper import helper
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as md
import numpy as np

adsb_data = pd.read_csv(r"C:\Users\bsmig\Documents\repos\adsb\logged_data\logged_ADSB_data_2021_04_03_0805.txt", names=ADSB_FIELDS)

# combine dcate and time into one column
adsb_data["when_message_generated"] = adsb_data["date_message_generated"] + " " + adsb_data["time_message_generated"]

# convert to datetime object
adsb_data["when_message_generated"] = pd.to_datetime(adsb_data["when_message_generated"])

# make sure table is sorted in time appropriately
adsb_data = adsb_data.sort_values(by='when_message_generated')


##############################################################################
## Compute number of aircraft seen per hour

fig, axs = plt.subplots(figsize=(12, 4))
n_aircraft_per_hour = adsb_data.groupby(adsb_data["when_message_generated"].dt.hour)["hex_address"].nunique().plot(kind='bar', rot=0, ax=axs)
plt.xlabel("Hour of the day");
plt.ylabel("Number of aircraft");

##############################################################################
## Compute when each callsign was seen
'''
hex_addr_and_callsigns = adsb_data[["hex_address", "callsign"]]
has_callsign = hex_addr_and_callsigns["callsign"].notna()
aa = hex_addr_and_callsigns[has_callsign].drop_duplicates()
'''

##############################################################################
## Show duration of each hex address
'''
plt.scatter(adsb_data["when_message_generated"].dt.hour, adsb_data["hex_address"])
plt.xlabel("Time of day")
plt.ylabel("Hex address")
#plt.gca().xaxis.set_major_locator(md.MinuteLocator(byminute = [0, 15, 30, 45]))
#plt.gca().xaxis.set_major_formatter(md.DateFormatter('%H'))
'''
##############################################################################
## Compute ranges to my QTH

hp = helper()
lla_data = adsb_data[["latitude","longitude","altitude"]]
good_llas_cond = lla_data.notnull().all(axis=1)
good_llas = lla_data[good_llas_cond]
ranges_m = good_llas.apply(lambda x: hp.compute_range_from_QTH(x), axis=1)

