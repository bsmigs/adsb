import numpy as np
import numpy.matlib
import time, datetime
from constants import *
from helper import *

class ADSB:
    def __init__(self,
                 origin_lat,
                 origin_lon,
                 origin_alt):
        
        self.my_flight_tuple         = {}
        self.max_range_seen          = 0
        self.qth_lla                 = np.array([origin_lat, origin_lon, origin_alt])
        self.h                       = helper(origin_lat, origin_lon, origin_alt)
        self.qth_ecef                = self.h.GetECEFPositionVectors(self.qth_lla)

    def get_num_aircraft(self):
        
        total_num_aircraft = 0
        for hex_addr in self.my_flight_tuple:
            total_num_aircraft += 1

    def get_QTH_lat(self):
        
        return self.qth_lla[0]

    def get_QTH_lon(self):
        
        return self.qth_lla[1]
    
    def get_callsign(self,
                     hex_addr):
        
        callsign = 'N/A'
        if ('callsign' in self.my_flight_tuple[hex_addr]):
            callsign = self.my_flight_tuple[hex_addr]['callsign']
            
        return callsign

    def get_flight_tuple(self,
                         hex_addr=None):
        
        aircraft_dict = {}
        if (hex_addr and hex_addr in self.my_flight_tuple):
            aircraft_dict = self.my_flight_tuple[hex_addr]
        
        return aircraft_dict

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
        
        data_tuple = {}
        
        # grab the message type
        msg_type = int(split_line[1])
        
        # unique hex address for current aircraft
        hex_addr = split_line[4] 
        
        if (split_line[5]):
            # flightID: database flight record number
            data_tuple['flight_ID'] = split_line[5]

        if (msg_type == 1 and split_line[10]):
            # callsign (may not be available)
            data_tuple['callsign'] = split_line[10]
    
        if (msg_type == 3):
            # year-month-day
            ymd = split_line[6] 
            # hours-mins-sec
            hms = split_line[7] 
            # convert date/time to epoch to better work with it
            epoch = self.h.convert_to_epoch(ymd, hms)
            data_tuple['last_observed'] = np.array(epoch)
            # altitude (ft)
            alt = float(split_line[11])
            # latitude (deg)
            lat = float(split_line[14])
            # longitude (deg)
            lon = float(split_line[15])
            data_tuple['lla'] = np.array([lat, lon, alt])
            #data_tuple['range'] = np.array(self.h.compute_range_from_QTH(data_tuple['lla'])) # (m)
            
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
        #data_tuple['speed'] = np.array(0)
    
        return hex_addr, data_tuple

    def update_data(self,
                    hex_addr,
                    data_tuple):
        
        # for prop in list(data_tuple.keys()):
        #     if (prop == 'lla' and prop in self.my_flight_tuple[hex_addr]):
        #         self.my_flight_tuple[hex_addr][prop] = np.vstack((data_tuple[prop], self.my_flight_tuple[hex_addr][prop]))
                
        #         if (np.size(self.my_flight_tuple[hex_addr][prop]) > NUM_MAX_DATA):
        #             # pop off oldest element
        #             np.delete(self.my_flight_tuple[hex_addr][prop], -1, 0)
        #     else:
        #         self.my_flight_tuple[hex_addr][prop] = data_tuple[prop]

        for prop in list(data_tuple.keys()):
            if (prop == 'lla'):
                if (prop not in self.my_flight_tuple[hex_addr]):
                    self.my_flight_tuple[hex_addr][prop] = data_tuple[prop]
                    
                    print("Added aircraft",hex_addr)
                else:
                    self.my_flight_tuple[hex_addr][prop] = np.vstack((data_tuple[prop], self.my_flight_tuple[hex_addr][prop]))
                
                if (np.size(self.my_flight_tuple[hex_addr][prop]) > NUM_MAX_DATA):
                    # pop off oldest element
                    np.delete(self.my_flight_tuple[hex_addr][prop], -1, 0)
            else:
                self.my_flight_tuple[hex_addr][prop] = data_tuple[prop]


    def update_flight_tuple(self, 
                            hex_addr, 
                            data_tuple):
        
        # check to see if it's empty
        if (len(hex_addr)==0 and len(data_tuple)==0):
            return
        
        if (hex_addr in self.my_flight_tuple):
            # want to update data_tuple fields bearing 
            # in mind that we will eliminate entries when 
            # we have exceeded the maximum cached number 
            # of elements
            self.update_data(hex_addr, data_tuple)
        else:
            # if current aircraft not yet observed, store the 
            # first time it was seen
            self.my_flight_tuple[hex_addr] = data_tuple


    def delete_aircraft(self):
        
        # loop through all the aircrafts we have and ask
        # if the last time we received an update from them
        # exceeds our max time limit to get an update
        
        # if no airplanes logged yet, just return
        if (np.size(self.my_flight_tuple) == 0):
            return

        # compute time once for all aircraft
        curr_time = time.mktime( datetime.datetime.now().timetuple() )
        
        # loop through all the planes and delete if necessary
        for hex_addr in list(self.my_flight_tuple.keys()):
            if ('last_observed' in self.my_flight_tuple[hex_addr]):
                last_time_observed = self.my_flight_tuple[hex_addr]['last_observed']
                if (curr_time - last_time_observed > MAX_TIME_UNOBSERVED):
                    
                    delete_str = self.h.convert_epoch_to_datestr(last_time_observed)
                    print("deleted aircraft", hex_addr,"after", curr_time - last_time_observed, "(s) since last observed")

                    del self.my_flight_tuple[hex_addr]

    def process_new_messages(self, 
                             split_line):
        
        #print(split_line)
        
        # parse the new line of data
        updated_hex_addr, data_tuple = self.parse_new_data(split_line)
        
        # update tuples with new info
        self.update_flight_tuple(updated_hex_addr, data_tuple)
        
        # now delete old data, if applicable
        self.delete_aircraft()
            
        # return the hex address of the updated aircraft
        return updated_hex_addr
    
    def get_current_lats_lons(self):
        
        # start logic to plot here
        all_lats = np.array([])
        all_lons = np.array([])
        plot_colors = []
        
        #print(self.my_flight_tuple.keys())
        
        for hex_addr in self.my_flight_tuple:
            if ('lla' in self.my_flight_tuple[hex_addr].keys()):
                curr_data = np.array(self.my_flight_tuple[hex_addr]['lla'])
                
                curr_lats = curr_data[...,0]
                curr_lons = curr_data[...,1]
                
                all_lats = np.append(all_lats, curr_lats)
                all_lons = np.append(all_lons, curr_lons)
                
    def get_current_lats_lons_2(self):
        
        # start logic to plot here
        lats = {}
        lons = {}
        plot_colors = []
        
        #print(self.my_flight_tuple.keys())
        for hex_addr in self.my_flight_tuple:
            if ('lla' in self.my_flight_tuple[hex_addr].keys()):
                lla_data = self.my_flight_tuple[hex_addr]['lla']
                if (np.size(lla_data[...,0]) == 1 and np.size(lla_data[...,1]) == 1):
                    lats[hex_addr] = [lla_data[...,0]]
                    lons[hex_addr] = [lla_data[...,1]]
                else:
                    lats[hex_addr] = lla_data[...,0]
                    lons[hex_addr] = lla_data[...,1]
                
                
        return lats, lons

    def find_max_range_seen(self):
        
        for key in self.my_flight_tuple.keys():
            range = self.get_most_recent_quantity(key, 'range')
            if (range > self.max_range_seen):
                self.max_range_seen = range 
                max_range_hex_addr = key
                print("ICAO address",max_range_hex_addr,"is farthest plane at range {:.1f}".format(self.max_range_seen/1000),"(km)")


