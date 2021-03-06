# To be used with python3

import socket
import pyproj
import os, sys
os.environ["PROJ_LIB"] = r'C:\Users\bsmig\Anaconda3\envs\env\Library\share (location of epsg)'
import datetime
import numpy as np
import matplotlib.pyplot as plt
#import sqlite3
#from sqlite3 import Error
from ADSB import ADSB
from mpl_toolkits.basemap import Basemap
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
from curseXcel import Table
from helper import convert_epoch_to_datestr
import curses

HOST                = "192.168.1.77" # RPi IP address
PORT                = 30003 # dump1090 port we are listening to
BUFFER_SIZE         = 1024 # make it nice and big
QTH_LAT             = 42.647690 # my home's latitude
QTH_LON             = -71.253783 # my home's longitude
QTH_ALT             = 0 # my home's altitude (need to convert to ASL)
LOGAN_LAT           = 42.3656 # Logan latitude
LOGAN_LON           = -71.0096 # Logan longitude
MANCHESTER_LAT      = 42.9297 # Manchester lat
MANCHESTER_LON      = -71.4352 # Manchester lon
DEFAULT_COLOR_PAIR  = 1

# create ADS-B object
adsb                = ADSB(QTH_LAT, QTH_LON, QTH_ALT)

#------------------------------------------------------------
# set up figure and animation

# define/initialize plots for animation
myLowerLon          = -74.5
myLowerLat          = 40.5
myUpperLon          = -68
myUpperLat          = 46

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
    
# create and open a socket connection
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Socket made...")
s.connect( (HOST, PORT) )
print("Socket connected...")

def curses_main(stdscr):
    # orig_size output is (y,x)
    orig_size = stdscr.getmaxyx()
    
    col_names = ['Aircraft num', 'ICAO address', 'Callsign', 'Lat (deg)', 'Lon (deg)', 'Alt (ft)', 'Range (km)', 'Last seen']
    
    table_width = orig_size[1] 
    table_height = orig_size[0] 
    n_cols = len(col_names)
    n_rows = round(0.9*table_height)
    cell_width = round(0.9*table_width/n_cols)
    table = Table(stdscr, n_rows, n_cols, cell_width, table_width, table_height, col_names=True, spacing=1)
    
    col = 0
    while col < n_cols:
        table.set_column_header(col_names[col], col)
        col += 1
        
    entry_row_tuple = {}
    entry_row_number = 0
    screen_key = 0
    try:
        # q in ASCII is 113
        while (True and screen_key != ord('q')):
            screen_key = stdscr.getch()
            
            '''
            # Check if screen was re-sized (True or False)
            resize = curses.is_term_resized(orig_size[0], orig_size[1])
            
            # Action in loop if resize is True:
            if resize is True:
                
                y, x = stdscr.getmaxyx()
                
                print("resizing window with values y=",y,",x=",x)
                
                stdscr.clear()
                curses.resizeterm(y, x)
                stdscr.refresh()
            '''
    
        
            # grab current buffer. Returns bytes in python3
            curr_bytes_data = s.recv(BUFFER_SIZE)
            # convert bytes to string
            curr_str_data = curr_bytes_data.decode('utf-8')
            #print(curr_str_data)
    
            # process new messages
            adsb.process_new_messages(curr_str_data)
            
            # get current flight tuples
            flight_tuples = adsb.get_flight_tuple()
            
            # update fields in the table and add new fields 
            # that haven't been seen yet
            for hex_addr in flight_tuples:
                # we can only accommodate a number of
                # entries equal to n_rows. The column
                # headers already take up one row and
                # counting starts from 0, so
                # that's why we condition on n_rows-2
                if (len(entry_row_tuple) > n_rows-2):
                    continue
                
                if (hex_addr not in entry_row_tuple):
                    data_tuple = {}
                    data_tuple['row_number'] = entry_row_number
                    entry_row_tuple[hex_addr] = data_tuple
                    
                    # add a new row and populate it
                    table.set_cell(entry_row_number, 0, entry_row_number+1)
                    table.set_cell(entry_row_number, 1, hex_addr)
                    
                    # increment the counter
                    entry_row_number += 1
                    
                if ('callsign' in flight_tuples[hex_addr]):
                    entry_row_tuple[hex_addr]['callsign'] = flight_tuples[hex_addr]['callsign']
                    table.set_cell(entry_row_tuple[hex_addr]['row_number'], 2, flight_tuples[hex_addr]['callsign'])                    
                    
                if ('lla' in flight_tuples[hex_addr]):
                    lla = flight_tuples[hex_addr]['lla']
                    # update the other entries
                    if (np.ndim(lla) == 1):
                        lat = np.around(lla[0], 4)
                        lon = np.around(lla[1], 4)
                        alt = np.around(lla[2], 2)
                    else:
                        lat = np.around(lla[0,0], 4)
                        lon = np.around(lla[0,1], 4)
                        alt = np.around(lla[0,2], 2)
                    table.set_cell(entry_row_tuple[hex_addr]['row_number'], 3, lat)
                    table.set_cell(entry_row_tuple[hex_addr]['row_number'], 4, lon)
                    table.set_cell(entry_row_tuple[hex_addr]['row_number'], 5, alt)
                    
                if ('range' in flight_tuples[hex_addr]):
                    aircraft_range = np.around(adsb.get_most_recent_quantity(hex_addr, 'range')*1e-3, 1)
                    table.set_cell(entry_row_tuple[hex_addr]['row_number'], 6, aircraft_range)
                    
                if ('last_observed' in flight_tuples[hex_addr]):
                    last_seen = convert_epoch_to_datestr(adsb.get_most_recent_quantity(hex_addr, 'last_observed'))
                    table.set_cell(entry_row_tuple[hex_addr]['row_number'], 7, last_seen)
                
            # delete entries we haven't seen anymore
            # because ADSB class dropped them due to timeout
            # of new data
            for hex_addr in list(entry_row_tuple.keys()):
                if (hex_addr not in flight_tuples):
                    # delete row if not seen
                    table.delete_row(entry_row_tuple[hex_addr]['row_number'])
                    del entry_row_tuple[hex_addr]
            
            # relable the row numbers corresponding to aircraft
            # num since we deleted some of them from the table
            entry_row_number = 0
            for hex_addr in entry_row_tuple:
                entry_row_tuple[hex_addr]['row_number'] = entry_row_number
                table.set_cell(entry_row_tuple[hex_addr]['row_number'], 0, entry_row_number+1)
                table.set_cell(entry_row_tuple[hex_addr]['row_number'], 1, hex_addr)
                
                entry_row_number += 1
            
            table.refresh()

            # see if we've found any new aircraft in the sky        
            #adsb.get_num_aircraft()
                
            # display farthest seen aircraft
            #adsb.find_max_range_seen()
                
            # plot the new data
            #plot_updates()
            #plt.draw()
            #plt.pause(0.001)
            
    except KeyboardInterrupt:     
        print("Exiting out of program...")
    
    
def plot_data_main():
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
        # close the socket
        s.close()



def write_data_out_main():
    # create and open a socket connection
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Socket made...")
    s.connect( (HOST, PORT) )
    print("Socket connected...")
    
    # check if path exists already to log data
    filepath = "../logged_data"
    isdir = os.path.isdir(path) 
    if (not isdir):
        os.mkdir(filepath)
        
    # open a file and timestamp it
    timetuple = datetime.datetime.now().timetuple()
    yr = timetuple(0)
    mo = timetuple(1)
    dy = timetuple(2)
    hr = timetuple(3)
    mn = timetuple(4)
    sc = timetuple(5)
    filename = "logged_ADSB_data_"+str(yr)+"_"+str(mo)+"_"+str(dy)+"_"+str(hr)+"_"+str(mn)+"_"+str(sc)+".txt"
    myfile = open(filepath+"/"+filename, 'w')
    
    try:
        while (True):
            # grab current buffer. Returns bytes in python3
            curr_bytes_data = s.recv(BUFFER_SIZE)
            # convert bytes to string
            curr_str_data = curr_bytes_data.decode('utf-8')
            #print(curr_str_data)
    
            # process new messages
            adsb.process_new_messages(curr_str_data)
            
            # get current flight tuples
            flight_tuples = adsb.get_flight_tuple()
            
            # update fields in the table and add new fields 
            # that haven't been seen yet
            for hex_addr in flight_tuples:
                callsign_flag = False
                lla_flag = False
                time_flag = False
                
                # make sure callsign is there
                if ('callsign' in flight_tuples[hex_addr]):
                    callsign_flag = True
                    
                # make sure lla is there
                if ('lla' in flight_tuples[hex_addr]):
                    lla_flag = True
                    
                # make sure time is there
                if ('last_observed' in flight_tuples[hex_addr]):
                    time_flag = True
                    
                if (callsign_flag and lla_flag and time_flag):
                    callsign = flight_tuples[hex_addr]['callsign']
                    lla = flight_tuples[hex_addr]['lla']
                    # update the other entries
                    if (np.ndim(lla) == 1):
                        lat = np.around(lla[0], 4)
                        lon = np.around(lla[1], 4)
                        alt = np.around(lla[2], 2)
                    else:
                        lat = np.around(lla[0,0], 4)
                        lon = np.around(lla[0,1], 4)
                        alt = np.around(lla[0,2], 2)
                    last_seen = convert_epoch_to_datestr(adsb.get_most_recent_quantity(hex_addr, 'last_observed'))
                
                    # add data to file
                    myfile.write(callsign+"\t"+str(lat)+"\t"+str(lon)+"\t"+str(alt)+"\t"+last_seen)
    except KeyboardInterrupt:     
        print("Exiting out of program...")
        # close the file
        myfile.close()
        # close the socket
        s.close()



#plot_data_main()

stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.keypad(True)
# make sure getch() is non-blocking
stdscr.nodelay(True)
print("Can change terminal colors =", curses.can_change_color())
if (curses.can_change_color()):
    curses.start_color()
    curses.init_pair(DEFAULT_COLOR_PAIR, curses.COLOR_GREEN, curses.COLOR_WHITE)
    
# main workhorse
curses.wrapper(curses_main)


curses.nocbreak()
stdscr.keypad(False)
curses.echo()
curses.endwin()
print("Exiting out of program...")
s.close()


    


    
