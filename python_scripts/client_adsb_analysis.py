# To be used with python3

import socket
import pyproj
import os
os.environ["PROJ_LIB"] = r'C:\Users\bsmig\Anaconda3\envs\env\Library\share (location of epsg)'
import sys
import datetime
#import numpy as np
import matplotlib.pyplot as plt
#import sqlite3
#from sqlite3 import Error
from ADSB import *
from mpl_toolkits.basemap import Basemap
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation

HOST                = "192.168.1.77" # RPi IP address
PORT                = 30003 # dump1090 port we are listening to
BUFFER_SIZE         = 1024 # make it nice and big
QTH_LAT             = 42.647690 # my home's latitude
QTH_LON             = -71.253783 # my home's longitude
QTH_ALT             = 0 # my home's altitude (need to convert to ASL)
LOGAN_LAT             = 42.3656 # Logan latitude
LOGAN_LON             = -71.0096 # Logan longitude
MANCHESTER_LAT        = 42.9297 # Manchester lat
MANCHESTER_LON        = -71.4352 # Manchester lon
#EARTH_RADIUS         = 6366707.0 # (m)


# create ADS-B object
adsb                = ADSB(QTH_LAT, QTH_LON, QTH_ALT)


#------------------------------------------------------------
# set up figure and animation

def enu_to_geodetic(x_enu, y_enu, units):
    if (units == 'km'):
        x_enu *= 1000
        y_enu *= 1000

    ecef = pyproj.Proj(proj='geocent', ellps='WGS84', datum='WGS84')
    lla = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')
    
    # get my QTH's ecef vector derived from lat/lon
    x0_ecef_home, y0_ecef_home, z0_ecef_home = pyproj.transform(lla, ecef, QTH_LON, QTH_LAT, 0, radians=False)
    
    # now assuming ENU coord system centered on my
    # QTH, get the ecef vectors for the box
    x_max_ecef = x0_ecef_home + x_enu
    y_max_ecef = y0_ecef_home + y_enu
    
    x_min_ecef = x0_ecef_home - x_enu
    y_min_ecef = y0_ecef_home - y_enu
    
    lower_lon, lower_lat, lower_alt = pyproj.transform(ecef, lla, x_min_ecef, y_min_ecef, z0_ecef_home, radians=False)
    upper_lon, upper_lat, upper_alt = pyproj.transform(ecef, lla, x_max_ecef, y_max_ecef, z0_ecef_home, radians=False)
    
    return lower_lon, lower_lat, upper_lon, upper_lat

# define/initialize plots for animation

#maxEast_km     = 200
#maxNorth_km = 200
#myLowerLon, myLowerLat, myUpperLon, myUpperLat = enu_to_geodetic(maxEast_km, maxNorth_km, 'km')
#print(myLowerLon, myLowerLat, myUpperLon, myUpperLat)

myLowerLon     = -74.5
myLowerLat     = 40.5
myUpperLon     = -68
myUpperLat     = 46


'''
fig = plt.figure(1)
myMap = Basemap(projection = 'mill', llcrnrlat=myLowerLat, urcrnrlat=myUpperLat, \
                          llcrnrlon=myLowerLon, urcrnrlon=myUpperLon, resolution='c', \
                          lat_0=adsb.QTH_LAT, lon_0=adsb.QTH_LON)       
myMap.shadedrelief()
ln, = plt.plot([], [], 'ro', markersize=4)
plt.plot(QTH_LON, QTH_LAT, 'kx', markersize=8)
plt.plot(LOGAN_LON, LOGAN_LAT, 'bs', markersize=8)
plt.plot(MANCHESTER_LON, MANCHESTER_LAT, 'gs', markersize=8)
plt.xlim(myLowerLon, myUpperLon)
plt.ylim(myLowerLat, myUpperLat)
plt.xlabel('Longitude (deg)')
plt.ylabel('Latitude (deg)')
plt.ion()
'''

    
fig = plt.figure(1)
#ax = fig.add_subplot(111)
# miller projection
myMap = Basemap(projection = 'mill', llcrnrlat=myLowerLat, urcrnrlat=myUpperLat, llcrnrlon=myLowerLon, urcrnrlon=myUpperLon, resolution='c', lat_0=adsb.get_lat(), lon_0=adsb.get_lon())     
myMap.shadedrelief()
x0, y0 = myMap([adsb.get_lon()], [adsb.get_lat()])
x1, y1 = myMap([LOGAN_LON], [LOGAN_LAT])
x2, y2 = myMap([MANCHESTER_LON], [MANCHESTER_LAT])
myMap.plot(x0, y0, 'kx', x1, y1, 'bs', x2, y2, 'gs', markersize=8, latlon=False)[0]
point, = myMap.plot([], [], 'ro', markersize=4)
plt.xlabel('Longitude (deg)')
plt.ylabel('Latitude (deg)')

def animate(ii):    
    lats, lons = adsb.get_current_lats_lons()

    # convert lat/lon to x/y coords on map
    x_list, y_list = myMap(lons, lats)
    point.set_data(x_list, y_list)
    
    return point,

    
    
def plot_updates():
    # get current lats/lons
    lats, lons = adsb.get_current_lats_lons()
    
    # convert lat/lon to x/y coords on map
    x_list, y_list = myMap(lons, lats)
    point.set_data(x_list, y_list)
    point.set_marker('o')
    point.set_markerfacecolor('r')
    point.set_markeredgecolor('r')
    point.set_markersize(4)
    
    '''
    for key in adsb.my_flight_tuple:
        curr_data = np.array(adsb.my_flight_tuple[ key ])    
        rgb_color = adsb.color_dict[ key ]
        
        lats = curr_data[:,1]
        lons = curr_data[:,2]
        x_list, y_list = myMap(lons, lats)
        point.set_data(x_list, y_list)
        point.set_marker('o')
        point.set_markersize(4)
        point.set_markerfacecolor(rgb_color)
        point.set_markeredgecolor(rgb_color)
    '''
    
    
# create and open a socket connection
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Socket made...")
s.connect( (HOST, PORT) )
print("Socket connected...")


num_current_aircraft = 0
max_range = -1
max_range_hex_addr = ''
try:
    while (True):
        # grab current buffer. Returns bytes in python3
        curr_bytes_data = s.recv(BUFFER_SIZE)
        # convert bytes to string
        curr_str_data = curr_bytes_data.decode('utf-8')
        #print(curr_str_data)

        # process new messages
        adsb.process_new_messages(curr_str_data)

        # see if we've found any new aircraft in the sky        
        num_previous_aircraft = adsb.get_num_aircraft()
        if (num_current_aircraft != num_previous_aircraft):
            ts = datetime.datetime.now()
            
            num_current_aircraft = num_previous_aircraft
            print("time = ",ts,"; Number of distinct aircraft seen = ", num_current_aircraft)
            
        # display farthest seen aircraft
        for key in adsb.my_flight_tuple.keys():
            data = adsb.my_stored_data[key]
            range = data['max_range']
            if (range > max_range):
                max_range = range 
                max_range_hex_addr = key
                print("ICAO address",max_range_hex_addr,"is farthest plane at range {:.1f}".format(max_range/1000),"(km)")
            
        # plot the new data
        #plot_updates()
        #plt.draw()
        plt.pause(0.001)
        
except KeyboardInterrupt:     
    print("Exiting out of program...")
    s.close()




    


    
