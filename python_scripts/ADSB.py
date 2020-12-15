from GetENUVelocities import *
from GetHeadings import *
import numpy as np
import numpy.matlib
import random
import sys
import time
import datetime

N_DIFF_TRACKS              = 100
AIRCRAFT_ID_MSG            = 3
NUM_MAX_DATA               = 50 # number of aircraft to cache
MAX_TIME_UNOBSERVED        = 90 # (sec) amt of time elapsed before removing aircraft from cache
EARTH_RADIUS               = 6366707.0 # (m)


class ADSB:
    def __init__(self,
                 QTH_LAT,
                 QTH_LON,
                 QTH_ALT): 
        self.my_flight_tuple         = {}
        self.my_stored_data          = {}
        self.qth_lla                 = np.array([QTH_LAT, QTH_LON, QTH_ALT])
        self.qth_ecef                = ADSB.GetECEFPositionVectors(self.qth_lla)
        self.color_dict              = {}
        self.global_color_dict       = {'unused':ADSB.colors_for_plots(), 'used':[]}

    def get_num_aircraft(self):
        return len(self.my_flight_tuple)
    
    def get_lat(self):
        return self.qth_lla[0]
    
    def get_lon(self):
        return self.qth_lla[1]
    
    def get_alt(self):
        return self.qth_lla[2]
    
    def parse_new_data(self,
                       split_line):
        # using Malcolm Robb's dump1090 format
        # when executing with "net-sbs-port" option
        # and parse through the fields
        
        #print(split_line)
        
        # grab the message type
        msg_type = int(split_line[1]) 
    
        # unique hex address for current aircraft
        hex_addr = split_line[4] 
        # year-month-day
        ymd = split_line[6] 
        # hours-mins-sec
        hms = split_line[7] 

        if split_line[10]:
            # callsign (may not be available)
            callsign = split_line[10] 
        else:
            callsign = 'NaN'
    
        if split_line[11]:
            # altitude (ft) (may not be available)
            alt = float(split_line[11]) 
        else:
            #print("No valid altitude")
            alt = -1
    
        if split_line[12]:
            # ground speed (knots). (may not be available)
            ground_speed = float(split_line[12]) 
        else:
            ground_speed = 0

        if (split_line[13]):
            # heading (deg). (may not be available)
            heading = float(split_line[13]) 
        else:
            heading = 1000;
                        
        if (split_line[14]):
            # latitude (deg). (may not be available)
            lat = float(split_line[14]) 
        else:
            lat = 1000
            
        if (split_line[15]):
            # longitude (deg). (may not be available)
            lon = float(split_line[15]) 
        else:
            lon = 1000
            
        if (split_line[21]):
            # denotes if plane communicating it's on the gnd. (may not be available)
            on_the_gnd = split_line[21]
        else:
            on_the_gnd = 'NULL' 

        # convert date/time to epoch to better work with it
        epoch = ADSB.convert_to_epoch(ymd, hms)
    
        # gather needed data into a list
        data = np.array([epoch, lat, lon, alt])
        
        return msg_type, hex_addr, data

    def initialize_stored_data(self,
                               hex_addr, 
                               data):
        max_alt                       = data[3]
        aircraft_lla                  = data[1:4]
        aircraft_ecef                 = ADSB.GetECEFPositionVectors(aircraft_lla)
        aircraft_enu                  = ADSB.GetENUCoords(aircraft_lla, self.qth_lla) # (m)
        curr_range                    = float(np.linalg.norm(aircraft_enu))
        epoch                         = data[0]
        stored_data                   = {'first_observed':epoch, 'last_observed':epoch, 'max_range':curr_range, 'max_altitude':max_alt, 'max_speed':0}
    
        self.my_stored_data.update( {hex_addr : stored_data} )
        
        # assign the next available plot color to the 
        # aircraft and move that (r,g,b) tuple to the
        # "used" category
        curr_color                    = self.global_color_dict['unused'][0]
        self.color_dict[ hex_addr ]   = curr_color
        self.global_color_dict['used'].append(curr_color)

    def update_stored_data(self,
                           hex_addr, 
                           data):
                           
        # if we have at least 2 elements, we can begin
        # computing other quantities from the 2 most recent
        # data entries

        # convert aircraft coords to ENU centered at my QTH
        aircraft_lla = data[0,1:4]
        aircraft_enu = ADSB.GetENUCoords(aircraft_lla, self.qth_lla) # (m)
        
        # get ENU velocities
        #times = data[0:1+1, 0]
        #aircraft_velocities = GetENUVelocities(times, aircraft_enu)
        aircraft_velocities = np.mat([100, 100, 100])
    
        # get speeds
        enu_speeds = np.linalg.norm(aircraft_velocities, axis=1)
    
        # get headings
        #headings = GetHeadings(self.qth_enu, aircraft_enu);
        
        # current range of aircraft to my QTH
        curr_range = float(np.linalg.norm(aircraft_enu))
    
        stored_data = self.my_stored_data[ hex_addr ]
        if (curr_range > stored_data['max_range']):
            stored_data['max_range'] = curr_range
            
        if (aircraft_lla[2] > stored_data['max_altitude']):
            stored_data['max_altitude'] = aircraft_lla[2]

        if (enu_speeds[0] > stored_data['max_speed']):
            stored_data['max_speed'] = enu_speeds[0]

        most_recent_observed_time = data[0,0]
        stored_data['last_observed'] = most_recent_observed_time
                    
        # re-save data
        self.my_stored_data[ hex_addr ] = stored_data


    def update_flight_tuple(self, 
                            split_line):
                            
        msg_type, hex_addr, data = self.parse_new_data(split_line)
            
        if ( (msg_type == AIRCRAFT_ID_MSG) and (hex_addr in self.my_flight_tuple) ):
            values = self.my_flight_tuple[hex_addr]
            data = np.vstack((data, values)) # older values at the back

            # if we have at least 2 elements, we can begin
            # computing other quantities from the 2 most recent
            # data entries
            if (len(data) > 1):
                self.update_stored_data(hex_addr, data)

            # update until total amount of data equals what's
            # specified. Otherwise, pop off earliest entry and
            # move everything up accordingly. (FIFO)
            if (len(data) > NUM_MAX_DATA):
                data = np.delete(data, -1, 0) # pop off the oldest element
                
            # update the data entries
            self.my_flight_tuple[hex_addr] = data
                
        elif ( (msg_type == AIRCRAFT_ID_MSG) and (hex_addr not in self.my_flight_tuple) ):
            # if current aircraft not yet observed, store the 
            # first time it was seen
            self.initialize_stored_data(hex_addr, data)
            
            # update the data entries
            self.my_flight_tuple[hex_addr] = data
            
        elif ( (msg_type != AIRCRAFT_ID_MSG) and (hex_addr in self.my_flight_tuple) ):
            # if we are still getting updates but those updates do not
            # include the position info to perform calculations, then
            # just update the last time it was seen so the plane
            # does not go out of scope
            stored_data = self.my_stored_data[hex_addr]
            curr_time = time.mktime( datetime.datetime.now().timetuple() )
            stored_data['last_observed'] = curr_time
            self.my_stored_data[hex_addr] = stored_data
            
    def delete_aircraft(self):
        # loop through all the aircrafts we have and ask
        # if the last time we received an update from them
        # exceeds our max time limit to get an update

        # just compute time once for all aircraft
        curr_time = time.mktime( datetime.datetime.now().timetuple() )
        for key in list(self.my_stored_data.keys()):
            
            #print(curr_time, self.my_stored_data[key]['last_observed'], curr_time - self.my_stored_data[key]['last_observed'])
            
            if (curr_time - self.my_stored_data[key]['last_observed'] > MAX_TIME_UNOBSERVED):
                
                print("deleted aircraft", key,", time last seen was = ", self.my_stored_data[key]['last_observed'])
                
                del self.my_flight_tuple[key]
                del self.my_stored_data[key]
            
                # make the current color available again
                curr_color = self.color_dict[key]
                self.global_color_dict['used'].remove( curr_color )
                self.global_color_dict['unused'].append( curr_color )
            
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

            #print("start_idx = ",start_idx,", locations = ", locations,", len(curr_line) = ",len(curr_line))
            #print(split_line)

            if (len(split_line) != 22):
                start_idx = locations + 1
                continue

            self.update_flight_tuple(split_line)

            start_idx = locations + 1

        # now delete old data
        self.delete_aircraft()    

    def get_current_lats_lons(self):
        # start logic to plot here, I think
        lats = np.array([]) #[]
        lons = np.array([]) #[]
        plot_colors = []
        for key in self.my_flight_tuple:
            curr_data = np.array(self.my_flight_tuple[ key ])        
            lats = np.append(lats, curr_data[...,1])
            lons = np.append(lons, curr_data[...,2])
            
            #lats.append( curr_data[:,1] )
            #lons.append( curr_data[:,2] )
            #plot_colors.append(self.color_dict[ key ]) 
            
        return lats, lons
    
    @staticmethod
    def convert_to_epoch(ymd,
                         hms):
        # ymd = year, month, day
        # hms = hour, minute, second
        # convert date/time to epoch to better work with it
        date_time = str(ymd) + " " + str(hms)
        
        #print(date_time)
        
        pattern = '%Y/%m/%d %H:%M:%S.%f'
        epoch = time.mktime( time.strptime(date_time, pattern) )
        # get fractional seconds contribution to epoch
        epoch = epoch + float('.' + hms.split('.')[1])

        return epoch
    
    def GetECEFPositionVectors(lla):
        #phi = np.subtract(90, lats)
        #phi = np.deg2rad(phi)
        
        lats = np.deg2rad(lla[...,0])
        lons = np.deg2rad(lla[...,1])

        sinlat = np.sin(lats)
        coslat = np.cos(lats)
        sinlon = np.sin(lons)
        coslon = np.cos(lons)
        
        angle_vec = np.zeros(np.shape(lla))
        angle_vec[...,0] = np.multiply(coslat, coslon)
        angle_vec[...,1] = np.multiply(coslat, sinlon)
        angle_vec[...,2] = sinlat
        
        # need to repeat this 3 times (for 3 elements
        # of angle_vec
        radius_vec = EARTH_RADIUS*np.ones(np.shape(angle_vec))
        alts = lla[...,[2]]
        radius_vec = radius_vec + alts
        ecef_vec = np.multiply(radius_vec, angle_vec)
        
        return ecef_vec
    
    def GetENUCoords(aircraft_lla, qth_lla):
        qth_lat = np.deg2rad(qth_lla[0])
        qth_lon = np.deg2rad(qth_lla[1])
        
        coslat = np.cos(qth_lat)
        sinlat = np.sin(qth_lat)
        coslon = np.cos(qth_lon)
        sinlon = np.sin(qth_lon)
        
        rotation_mat = np.array([[-sinlon, coslon, 0], [-sinlat*coslon, -sinlat*sinlon, coslat], [coslat*coslon, coslat*sinlon, sinlat]])
        
        qth_ecef = ADSB.GetECEFPositionVectors(qth_lla)
        aircraft_ecef = ADSB.GetECEFPositionVectors(aircraft_lla)
        ecef_diff = aircraft_ecef - qth_ecef
        enu_vec = np.matmul(rotation_mat, ecef_diff)
        
        return enu_vec
    
    def colors_for_plots():
        ret = []
    
        r = int(random.random() * 256)
        g = int(random.random() * 256)
        b = int(random.random() * 256)
        step = 256 / N_DIFF_TRACKS
    
        for ii in range(N_DIFF_TRACKS):
            r += step
            g += step
            b += step
    
            r = int(r) % 256
            g = int(g) % 256
            b = int(b) % 256
        
            r0 = r/256.
            g0 = g/256.
            b0 = b/256.
    
            ret.append( (r0,g0,b0) ) 
        
        return ret
        


