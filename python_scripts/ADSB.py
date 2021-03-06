from GetENUVelocities import GetENUVelocities
from GetHeadings import GetHeadings
from helper import *
import numpy as np
import numpy.matlib
import random
import sys
import time
import datetime


N_DIFF_TRACKS              = 100
AIRCRAFT_ID_MSG            = 3
NUM_MAX_DATA               = 50 # number of aircraft to cache
MAX_TIME_UNOBSERVED        = 150 # (sec) amt of time elapsed before removing aircraft from cache
#EARTH_RADIUS               = 6366707.0 # (m)


class ADSB:
    def __init__(self,
                 QTH_LAT,
                 QTH_LON,
                 QTH_ALT): 
        self.my_flight_tuple         = {}
        self.total_num_aircraft      = 0
        self.max_range_seen          = 0
        self.qth_lla                 = np.array([QTH_LAT, QTH_LON, QTH_ALT])
        self.qth_ecef                = GetECEFPositionVectors(self.qth_lla)

    def get_num_aircraft(self):
        if (len(self.my_flight_tuple) > self.total_num_aircraft):
            self.total_num_aircraft = len(self.my_flight_tuple)
            ts = datetime.datetime.now()
            print("time = ",ts,"; Number of distinct aircraft seen = ", self.total_num_aircraft)
    
    def get_QTH_lat(self):
        return self.qth_lla[0]
    
    def get_QTH_lon(self):
        return self.qth_lla[1]
    
    def get_flight_tuple(self):
        return self.my_flight_tuple
    
    def get_most_recent_quantity(self,
                                 hex_addr,
                                 quantity):
        values = self.my_flight_tuple[hex_addr][quantity]
        if (np.ndim(values) == 0):
            # it's a scalar
            return values
        elif (np.ndim(values) == 1):
            # it's a vector
            return values[0]
        elif (np.ndim(values) == 2):
            # it's a 2D array
            return values[0,...]
    
    def parse_new_data(self,
                       split_line):
        # using Malcolm Robb's dump1090 format
        # when executing with "net-sbs-port" option
        # and parse through the fields
        
        #print(split_line)
        
        # put rest of data into a tuple
        data_tuple = {}
        
        # grab the message type
        msg_type = int(split_line[1])
        data_tuple['msg_type'] = msg_type
    
        # unique hex address for current aircraft
        hex_addr = split_line[4] 
        
        if (split_line[5]):
            # flightID: database flight record number
            data_tuple['flight_ID'] = split_line[5]
            
        # year-month-day
        ymd = split_line[6] 
        # hours-mins-sec
        hms = split_line[7] 
        # convert date/time to epoch to better work with it
        epoch = convert_to_epoch(ymd, hms)
        data_tuple['last_observed'] = np.array(epoch)

        if (msg_type == 1 and split_line[10]):
            # callsign (may not be available)
            data_tuple['callsign'] = split_line[10]
    
        if (msg_type == 3):
            # altitude (ft)
            alt = float(split_line[11]) 
            # latitude (deg)
            lat = float(split_line[14])
            # longitude (deg)
            lon = float(split_line[15])
            data_tuple['lla'] = np.array([lat, lon, alt])
            data_tuple['range'] = np.array(self.compute_range_from_QTH(data_tuple['lla'], self.qth_lla)) # (m)
    
        if (split_line[12]):
            # ground speed (knots). (may not be available)
            data_tuple['ground_speed'] = np.array(float(split_line[12]))
            
        if (split_line[13]):
            # track of aircraft (not heading). Derived from
            # the velocity E/W and velocity N/S
            data_tuple['track'] = np.array(float(split_line[13]))
            
        if (split_line[16]):
            # 64 ft resolution
            data_tuple['vertical_rate'] = np.array(float(split_line[16]))
            
        if (split_line[19]):
            # flag indicating if emergency code has been set
            data_tuple['emergency'] = bool(split_line[19])
            
        if (split_line[20]):
            # flag indicating transponder ident has been activated
            data_tuple['spi_ident'] = bool(split_line)
            
        if (split_line[21]):
            # denotes if plane communicating it's on the gnd. (may not be available)
            data_tuple['on_the_gnd'] = split_line[21]
        
        #aircraft_velocities = GetENUVelocities(times, aircraft_enu)
        aircraft_velocities = np.array([100, 100, 100])
        data_tuple['speed'] = np.array(0)
        
        return hex_addr, data_tuple
    
    def update_data(self,
                    hex_addr,
                    data_tuple):
        relevant_keys = ['lla', 'speed', 'ground_speed', 'range', 'track', 'last_observed']
        
        if ('callsign' in data_tuple):
            self.my_flight_tuple[hex_addr]['callsign'] = data_tuple['callsign']
        
        for key in relevant_keys:
            if (key in self.my_flight_tuple[hex_addr] and key in data_tuple):
                if (np.size(self.my_flight_tuple[hex_addr][key]) > NUM_MAX_DATA):
                    # pop off oldest element
                    np.delete(self.my_flight_tuple[hex_addr][key], -1, 0)
                
                # add newest to the front
                if (key == 'lla'):
                    # lla is a 1 x3 row vector, so need to
                    # vertical stack it
                    self.my_flight_tuple[hex_addr][key] = np.vstack((data_tuple[key], self.my_flight_tuple[hex_addr][key]))
                else:
                    # these are scalars, so horizontal stack
                    self.my_flight_tuple[hex_addr][key] = np.hstack((data_tuple[key], self.my_flight_tuple[hex_addr][key]))


    def update_flight_tuple(self, 
                            hex_addr, 
                            data_tuple):
        if (hex_addr in self.my_flight_tuple):
            # want to update data_tuple fields bearing 
            # in mind that we will eliminate entries when 
            # we have exceeded the maximum cached number 
            # of elements
            self.update_data(hex_addr, data_tuple)
        else:
            # if current aircraft not yet observed, store the 
            # first time it was seen
            data_tuple['first_observed'] = data_tuple['last_observed']
            self.my_flight_tuple[hex_addr] = data_tuple

    def delete_aircraft(self):
        # loop through all the aircrafts we have and ask
        # if the last time we received an update from them
        # exceeds our max time limit to get an update
        if (np.size(self.my_flight_tuple) == 0):
            return

        # just compute time once for all aircraft
        curr_time = time.mktime( datetime.datetime.now().timetuple() )
        for hex_addr in list(self.my_flight_tuple.keys()):
            if (curr_time - self.get_most_recent_quantity(hex_addr, 'last_observed') > MAX_TIME_UNOBSERVED):
                delete_str = convert_epoch_to_datestr(self.get_most_recent_quantity(hex_addr, 'last_observed'))
                #print("deleted aircraft", hex_addr,", time last seen was = ", delete_str)
                
                del self.my_flight_tuple[hex_addr]
            
    def process_new_messages(self, curr_line):
        # sometimes messages arrive at the same
         # time and the socket doesn't split them up by their
        # newline chars. So, do that manually
        start_idx = 0
        while (start_idx < len(curr_line)):
            locations = curr_line.find('\n', start_idx) # find a location of a new line char

            if (locations == -1):
                # when a new line char can't be found
                # the fcn returns -1. This happens
                # sometimes when the data comes in
                break

            # split the string up from starting point to new line char point
            new_line = curr_line[start_idx:locations] 
            # split strings based on commas from file to see what kind of msg type
            split_line = new_line.split(',')

            if (len(split_line) != 22):
                start_idx = locations + 1
                continue

            # parse the new line of data
            hex_addr, data_tuple = self.parse_new_data(split_line)
            
            # update tuples with new info
            self.update_flight_tuple(hex_addr, data_tuple)

            start_idx = locations + 1

        # now delete old data, if applicable
        self.delete_aircraft()

    def get_current_lats_lons(self):
        # start logic to plot here, I think
        lats = np.array([]) #[]
        lons = np.array([]) #[]
        plot_colors = []
        for key in self.my_flight_tuple:
            curr_data = np.array(self.my_flight_tuple[key]['data'])        
            lats = np.append(lats, curr_data[...,1])
            lons = np.append(lons, curr_data[...,2])
            
        return lats, lons
    
    def find_max_range_seen(self):
        for key in self.my_flight_tuple.keys():
            range = self.get_most_recent_quantity(key, 'range')
            if (range > self.max_range_seen):
                self.max_range_seen = range 
                max_range_hex_addr = key
                print("ICAO address",max_range_hex_addr,"is farthest plane at range {:.1f}".format(self.max_range_seen/1000),"(km)")


