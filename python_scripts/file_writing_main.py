import os, sys
os.environ["PROJ_LIB"] = r'C:\Users\bsmig\Anaconda3\envs\env\Library\share (location of epsg)'
import datetime
import numpy as np
from helper import convert_epoch_to_datestr
from constants import *
from ADSB import ADSB
import socket


file_writing_start_time = datetime.datetime(2021,3,16,9,00,0).timestamp()
file_writing_stop_time = datetime.datetime(2021,3,16,16,00,0).timestamp()

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


def main():
    # create and open a socket connection
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Socket made...")
    s.connect((HOST, PORT))
    print("Socket connected...")
    
    # create ADS-B object
    adsb = ADSB(QTH_LAT, QTH_LON, QTH_ALT)
    
    num_GB_used = 0

    
    # check if path exists already to log data
    filepath = "../logged_data"
    isdir = os.path.isdir(filepath) 
    if (not isdir):
        os.mkdir(filepath)
    
    # create the file to log data to
    filename = create_filename()
    myfile = open(filepath+"/"+filename, 'w')
    run_flag = True
    try:
        while (run_flag):
            # grab current buffer. Returns bytes in python3
            curr_bytes_data = s.recv(BUFFER_SIZE)
            # convert bytes to string
            curr_str_data = curr_bytes_data.decode('utf-8')
            
            #print(curr_str_data)
    
            # process new messages
            hex_addr = adsb.process_new_messages(curr_str_data)
            
            #print(flight_tuple)
            flight_tuple = adsb.get_flight_tuple(hex_addr)
            
            if (flight_tuple):
                if (flight_tuple['did_lla_update']):
                    lla = flight_tuple['lla']
                    # update the other entries
                    if (np.ndim(lla) == 1):
                        lat = lla[0]
                        lon = lla[1]
                        alt = lla[2]
                    else:
                        lat = lla[0,0]
                        lon = lla[0,1]
                        alt = lla[0,2]
                    last_seen = convert_epoch_to_datestr(adsb.get_most_recent_quantity(hex_addr, 'last_observed'))
                
                    # write to file if it's at the right time
                    current_epoch_time = datetime.datetime.now().timestamp()                    
                    if (current_epoch_time >= file_writing_start_time):
                        myfile.write(hex_addr+" "+str(lat)+" "+str(lon)+" "+str(alt)+" "+last_seen+"\n")
                        num_GB_used = myfile.tell()/1e9

                    if (current_epoch_time > file_writing_stop_time or num_GB_used > MAX_FILE_SIZE_GB):
                        run_flag = False
                        myfile.close()
                        print("Stopped writing file at ",datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
                        
    except KeyboardInterrupt:
        print("Exiting out of program...")
        # close the file
        myfile.close()
        # close the socket
        s.close()

