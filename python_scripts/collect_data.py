import os, sys
os.environ["PROJ_LIB"] = r'C:\Users\bsmig\Anaconda3\envs\env\Library\share (location of epsg)'
import datetime
import numpy as np
from constants import *
from ADSB import ADSB
import socket

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
            file_writing_start_time = datetime.datetime(yr,mo,dy,8,00,0).timestamp()
            file_writing_stop_time = datetime.datetime(yr,mo,dy,20,00,0).timestamp()

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
                    print("Started writing file at ",datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
                
                # write out data to file if it's the right time
                elif ((current_epoch_time >= file_writing_start_time and current_epoch_time <= file_writing_stop_time) and myfile != -1):
                    # drop the newline char
                    myfile.write(curr_str_data[0:new_line_loc])
                    num_GB_used = myfile.tell()/1e9

                # if we passed end time, stop writing data
                elif ((current_epoch_time > file_writing_stop_time or num_GB_used > MAX_FILE_SIZE_GB) and myfile != -1):
                    #run_flag = False
                    myfile.close()
                    num_GB_used = 0
                    myfile = -1
                    print("Stopped writing file at ",datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
            

    except KeyboardInterrupt:
        print("Exiting out of program...")
        # close the file
        myfile.close()
        # close the socket
        s.close()

if __name__ == "__main__":
    main()
