# -*- coding: utf-8 -*-
"""
Created on Sat Dec 19 18:17:10 2020

@author: bsmig
"""

import time
import datetime
import numpy as np

EARTH_RADIUS               = 6366707.0 # (m)


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

def convert_epoch_to_datestr(epoch_time):
    my_time = datetime.datetime.fromtimestamp(epoch_time)
    my_time_str = time.strftime("%Y-%m-%d %H:%M:%S", my_time.timetuple())
    
    return my_time_str

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

def GetENUCoords(aircraft_lla, 
                 qth_lla):
    qth_lat = np.deg2rad(qth_lla[0])
    qth_lon = np.deg2rad(qth_lla[1])
    
    coslat = np.cos(qth_lat)
    sinlat = np.sin(qth_lat)
    coslon = np.cos(qth_lon)
    sinlon = np.sin(qth_lon)
    
    rotation_mat = np.array([[-sinlon, coslon, 0], [-sinlat*coslon, -sinlat*sinlon, coslat], [coslat*coslon, coslat*sinlon, sinlat]])
    
    qth_ecef = GetECEFPositionVectors(qth_lla)
    aircraft_ecef = GetECEFPositionVectors(aircraft_lla)
    ecef_diff = aircraft_ecef - qth_ecef
    enu_vec = np.matmul(rotation_mat, ecef_diff)
    
    return enu_vec

def compute_range_from_QTH(aircraft_lla,
                           qth_lla):
        aircraft_enu = GetENUCoords(aircraft_lla, qth_lla) # (m)
        range = float(np.linalg.norm(aircraft_enu))
        
        return range
    