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
from ADSB import ADSB
from mpl_toolkits.basemap import Basemap
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
import curses

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

# create ADS-B object
adsb                = ADSB(QTH_LAT, QTH_LON, QTH_ALT)

#------------------------------------------------------------
# set up figure and animation

# define/initialize plots for animation
myLowerLon     = -74.5
myLowerLat     = 40.5
myUpperLon     = -68
myUpperLat     = 46


'''
fig = plt.figure(1)
myMap = Basemap(projection = 'mill', llcrnrlat=myLowerLat, urcrnrlat=myUpperLat, llcrnrlon=myLowerLon, urcrnrlon=myUpperLon, resolution='c', lat_0=adsb.QTH_LAT, lon_0=adsb.QTH_LON)       
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

'''
fig                             = plt.figure(1)
#ax                              = fig.add_subplot(111)
# miller projection
myMap                           = Basemap(projection = 'mill', llcrnrlat=myLowerLat, urcrnrlat=myUpperLat, llcrnrlon=myLowerLon, urcrnrlon=myUpperLon, resolution='c', lat_0=adsb.get_lat(), lon_0=adsb.get_lon())

myMap.shadedrelief()
x0, y0                          = myMap([adsb.get_lon()], [adsb.get_lat()])
x1, y1                          = myMap([LOGAN_LON], [LOGAN_LAT])
x2, y2                          = myMap([MANCHESTER_LON], [MANCHESTER_LAT])
myMap.plot(x0, y0, 'kx', x1, y1, 'bs', x2, y2, 'gs', markersize=8, latlon=False)[0]

point,                          = myMap.plot([], [], 'ro', markersize=4)
plt.xlabel('Longitude (deg)')
plt.ylabel('Latitude (deg)')
'''

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

def main(stdscr):
    
    stdscr.clear()
    
    
    
    
    # create and open a socket connection
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Socket made...")
    s.connect( (HOST, PORT) )
    print("Socket connected...")
    
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
            adsb.get_num_aircraft()
                
            # display farthest seen aircraft
            adsb.find_max_range_seen()
                
            # plot the new data
            #plot_updates()
            #plt.draw()
            #plt.pause(0.001)
            
    except KeyboardInterrupt:     
        print("Exiting out of program...")
        s.close()



if __name__ == "__main__":
    curses.wrapper(main)




    


    
