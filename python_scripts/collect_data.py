import os, sys, datetime, threading, time
from constants import *
os.environ["PROJ_LIB"] = OS_ENV_PATH
import matplotlib.pyplot as plt
import numpy as np
from ADSB import ADSB
import socket
from mpl_toolkits.basemap import Basemap
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation



# create an ADSB object
adsb = ADSB(GROUND_NODE_LAT, GROUND_NODE_LON, GROUND_NODE_ALT)

def animate(ii):    
    lats, lons = adsb.get_current_lats_lons()
    
    # convert lat/lon to x/y coords on map
    x_list, y_list = myMap(lons, lats)
    
    # add data to the map
    point.set_data(x_list, y_list)
    
    return point,


def plot_updates(thread_id):
    # create figure for visualization
    fig = plt.figure(1)
    #plt.figure(1)
    # miller projection
    myMap = Basemap(projection = 'mill', llcrnrlat=MY_LOWER_LAT, urcrnrlat=MY_UPPER_LAT, llcrnrlon=MY_LOWER_LON, urcrnrlon=MY_UPPER_LON, resolution='i', lat_0=GROUND_NODE_LAT, lon_0=GROUND_NODE_LON)
    myMap.shadedrelief()
   
    x0, y0 = myMap([GROUND_NODE_LON], [GROUND_NODE_LAT])
    x1, y1 = myMap([LOGAN_LON], [LOGAN_LAT])
    x2, y2 = myMap([MANCHESTER_LON], [MANCHESTER_LAT])
    x3, y3 = myMap([QTH_LON], [QTH_LAT])
    myMap.plot(x0, y0, 'kx', x1, y1, 'bs', x2, y2, 'rs', x3, y3, 'ks', markersize=4, latlon=False)[0]
    point, = myMap.plot([], [], 'ro', markersize=4)
    plt.xlabel('Longitude (deg)')
    plt.ylabel('Latitude (deg)')
    #plt.show(block=True)
    
    old_texts = []
    while (True):
        # get current lats/lons
        lats, lons = adsb.get_current_lats_lons_2()
        
        if (len(old_texts) > 0):
            for text in old_texts:
                text.set_visible(False)
            old_texts = []

        all_x = []
        all_y = []
        for hex_addr in list(lats.keys()):
            # convert lat/lon to x/y coords on map
            x_list, y_list = myMap(lons[hex_addr], lats[hex_addr])
            all_x.append(x_list)
            all_y.append(y_list)
            
            text = plt.text(x_list[0], y_list[0], adsb.get_callsign(hex_addr),fontsize=8, ha='left',va='bottom',color='k')
            old_texts.append(text)
            
        if (len(all_x) > 0):
            all_x = list(np.concatenate(all_x).flat)
            all_y = list(np.concatenate(all_y).flat)
            #print(all_x)
            
        point.set_data(all_x, all_y)
        point.set_marker('o')
        point.set_markerfacecolor('r')
        point.set_markeredgecolor('r')
        point.set_markersize(2)

            
        
        #fig.canvas.draw()
        plt.draw()
        plt.pause(0.001)
        #time.sleep(0.001)


def create_filename():
    # open a file and timestamp it
    timetuple = datetime.datetime.now().timetuple()
    
    #print(timetuple)
    
    yr = str(timetuple.tm_year)
    mo = str(timetuple.tm_mon)
    dy = str(timetuple.tm_mday)
    hr = str(timetuple.tm_hour)
    mn = str(timetuple.tm_min)
    
    if (len(yr)==1):
        yr="0"+yr
    if (len(mo)==1):
        mo="0"+mo
    if (len(dy)==1):
        dy="0"+dy
    if (len(hr)==1):
        hr="0"+hr
    if (len(mn)==1):
        mn="0"+mn
    
    filename = "logged_ADSB_data_"+yr+"_"+mo+"_"+dy+"_"+hr+mn+".txt"
    return filename


def collect_and_log_data(thread_id):
    
    # create and open a socket connection
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Socket made...")
    s.connect((HOST, PORT))
    print("Socket connected...")
    
    num_GB_used = 0
    
    # check if path exists already to log data
    filepath = "../logged_data"
    isdir = os.path.isdir(filepath) 
    if (not isdir):
        os.mkdir(filepath)

    myfile = -1
    run_flag = True
    try:
        while (run_flag):
            # set the file writing time for the current day
            timetuple = datetime.datetime.now().timetuple()
            yr = timetuple.tm_year
            mo = timetuple.tm_mon
            dy = timetuple.tm_mday
            file_writing_start_time = datetime.datetime(yr,mo,dy,6,00,0).timestamp()
            file_writing_stop_time = datetime.datetime(yr,mo,dy,23,59,0).timestamp()
    
            # grab current buffer. Returns bytes in python3
            curr_bytes_data = s.recv(BUFFER_SIZE)
            # convert bytes to string
            curr_str_data = curr_bytes_data.decode('utf-8')
            # find a location of a new line char
            new_line_loc = curr_str_data.find('\n', 0) 
            # split the string up from starting point to new line char point
            new_line = curr_str_data[0:new_line_loc] 
            # split strings based on commas from file to see what kind of msg type
            split_line = new_line.split(',')
            
            # check to see if we have a valid string or not
            if(len(split_line) == LEN_OF_VALID_STRING):
                current_epoch_time = datetime.datetime.now().timestamp()
                # open the file for writing when it's the right time
                if ((current_epoch_time >= file_writing_start_time and current_epoch_time <= file_writing_stop_time) and myfile == -1):
                    filename = create_filename()
                    myfile = open(filepath+"/"+filename, 'w')
                    print("Started writing file at",datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'))

                # write out data to file if it's the right time
                elif ((current_epoch_time >= file_writing_start_time and current_epoch_time <= file_writing_stop_time) and myfile != -1):
                    # drop the newline char
                    myfile.write(curr_str_data[0:new_line_loc])
                    num_GB_used = myfile.tell()/1e9
                    
                    # add the new data to the ADSB object
                    adsb.process_new_messages(split_line)
                    
                # if we passed end time, stop writing data
                elif ((current_epoch_time > file_writing_stop_time or num_GB_used > MAX_FILE_SIZE_GB) and myfile != -1):
                    #run_flag = False
                    myfile.close()
                    num_GB_used = 0
                    myfile = -1
                    print("Stopped writing file at",datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'))

    except KeyboardInterrupt:
        print("Exiting out of program...")
        # close the file
        myfile.close()
        # close the socket
        s.close()


if __name__ == "__main__":
    
    # create two threads here:
    # Thread 1: runs the main function which logs the data
    # Thread 2: plots the data stored in the ADSB object
    #t1 = threading.Thread(target=collect_and_log_data, args=(0,))
    t = threading.Thread(target=plot_updates, args=(1,), daemon=True)
    
    #t1.start()
    t.start()
    
    collect_and_log_data(0)
    
    #t1.join()
    t.join()
