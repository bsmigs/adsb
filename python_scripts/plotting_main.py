import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
from constants import *
from ADSB import ADSB
import socket



# create and open a socket connection
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Socket made...")
s.connect( (HOST, PORT) )
print("Socket connected...")

# create ADS-B object
adsb                = ADSB(QTH_LAT, QTH_LON, QTH_ALT)




#------------------------------------------------------------
# set up figure and animation


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
myMap                           = Basemap(projection = 'mill', llcrnrlat=myLowerLat, urcrnrlat=myUpperLat, llcrnrlon=myLowerLon, urcrnrlon=myUpperLon, resolution='c', lat_0=adsb.get_QTH_lat(), lon_0=adsb.get_QTH_lon())

myMap.shadedrelief()
x0, y0                          = myMap([adsb.get_QTH_lon()], [adsb.get_QTH_lat()])
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
    

def plot_data_main():
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
        # close the socket
        s.close()



