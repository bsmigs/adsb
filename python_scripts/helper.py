import time, datetime
import numpy as np
from constants import *

class helper:
    def __init__(self,
                 origin_lat,
                 origin_lon,
                 origin_alt): 
        
        self.qth_lla                 = np.array([origin_lat, origin_lon, origin_alt])
        self.qth_ecef                = self.GetECEFPositionVectors(self.qth_lla)

    def convert_to_epoch(self,
                         ymd,
                         hms):
        
        # ymd = year, month, day
        # hms = hour, minute, second
        # convert date/time to epoch to better work with it
        date_time = str(ymd) + " " + str(hms)
        
        pattern = '%Y/%m/%d %H:%M:%S.%f'
        epoch = time.mktime( time.strptime(date_time, pattern) )
        # get fractional seconds contribution to epoch
        epoch = epoch + float('.' + hms.split('.')[1])
    
        return epoch
    
    def convert_epoch_to_datestr(self,
                                 epoch_time):
        
        return datetime.datetime.fromtimestamp(epoch_time).strftime("%Y-%m-%d %H:%M:%S.%f")
    
    def GetECEFPositionVectors(self,
                               lla):
        lat = np.deg2rad(lla[0])
        lon = np.deg2rad(lla[1])
        alt = lla[2]*FT_TO_M
    
        sinlat = np.sin(lat)
        coslat = np.cos(lat)
        sinlon = np.sin(lon)
        coslon = np.cos(lon)
        
        N = WGS84_SEMIMAJOR_AXIS / np.sqrt(1-WGS84_ECCENTRICITY*WGS84_ECCENTRICITY*sinlat*sinlat)
        
        ecef_vec = np.zeros(np.shape(lla))
        ecef_vec[0] = (N + alt)*coslat*coslon
        ecef_vec[1] = (N + alt)*coslat*sinlon
        ecef_vec[2] = (N + alt)*sinlat
        
        return ecef_vec
    
    def GetENUCoords(self,
                     aircraft_lla):
        
        qth_lat = np.deg2rad(self.qth_lla[0])
        qth_lon = np.deg2rad(self.qth_lla[1])
        
        coslat = np.cos(qth_lat)
        sinlat = np.sin(qth_lat)
        coslon = np.cos(qth_lon)
        sinlon = np.sin(qth_lon)
        
        rotation_mat = np.array([[-sinlon, coslon, 0], [-sinlat*coslon, -sinlat*sinlon, coslat], [coslat*coslon, coslat*sinlon, sinlat]])
        
        #qth_ecef = GetECEFPositionVectors(np.array([QTH_LAT, QTH_LON, QTH_ALT]))
        aircraft_ecef = self.GetECEFPositionVectors(aircraft_lla)
        #ecef_diff = aircraft_ecef - qth_ecef
        ecef_diff = aircraft_ecef - self.qth_ecef
        enu_vec = np.matmul(rotation_mat, ecef_diff)
        
        return enu_vec
    
    def GetENUVelocities(self,
                         times,
                         enu_vec):

        # calculate position differences from btwn 2 consecutive times
        pos_diff = np.diff(enu_vec, axis=0)
        vec_size = np.shape(pos_diff)
    
        # calculate time interval
        time_diff = np.diff(times, axis=0).reshape((vec_size[0], 1))
    
        #print np.shape(times),np.shape(enu_vec),np.shape(pos_diff),np.shape(time_diff)
        #print "time_diff = ",time_diff
        #print "pos_diff = ",pos_diff
    
        # divide to get time
        enu_vels = np.divide(pos_diff, time_diff)
    
        return enu_vels
    
    def compute_range_from_QTH(self,
                               aircraft_lla):
        
        aircraft_enu = self.GetENUCoords(aircraft_lla) # (m)
        range = float(np.linalg.norm(aircraft_enu))
        
        return range
        
    def GetHeadings(self,
                    enu_vel_vec):

        # project aircraft coords onto E-N plane and normalize
        proj_aircraft = enu_vel_vec[:,0:2]
        # keep it an (N x 1) entity
        norm_factor = np.linalg.norm(proj_aircraft, axis=1, keepdims=True) 
        proj_aircraft = np.divide(proj_aircraft, norm_factor)
    
        # define local north unit vector and repeat as many
        # times necessary
        north = np.mat([0, 1])
        enu_vec_size = np.shape(enu_vel_vec)
        north = np.repeat(north, enu_vec_size[0], axis=0)
    
        # get the headings by taking dot product of north
        # unit vector with aircraft projected coords
        axis_dim = 1
        dot_prod = np.multiply(north, proj_aircraft).sum(axis_dim)
        headings = np.arccos(dot_prod)
    
        # the dot product will ALWAYS give us the smallest angle
        # between 2 vectors. If we wish to capture the larger one
        # need to put in a check that if the east coordinate is < 0
        # we then take (2*pi - original heading)
        condlist = [proj_aircraft[:,0] < 0, proj_aircraft[:,0] >= 0]
        choicelist = [2*np.pi - headings, headings]
        headings = np.select(condlist, choicelist)
        headings = np.rad2deg(headings)
    
        return headings