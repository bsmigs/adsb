import time
import datetime
import numpy as np
from constants import *

class helper:
    def __init__(self): 
        self.qth_lla                 = np.array([QTH_LAT, QTH_LON, QTH_ALT])
        self.qth_ecef                = self.GetECEFPositionVectors(self.qth_lla)

    def convert_to_epoch(self,
                         ymd,
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
    
    def convert_epoch_to_datestr(epoch_time):
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
    
    def compute_range_from_QTH(self,
                               aircraft_lla):
            aircraft_enu = self.GetENUCoords(aircraft_lla) # (m)
            range = float(np.linalg.norm(aircraft_enu))
            
            return range
        