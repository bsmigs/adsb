import matplotlib.pyplot as plt
import numpy as np
from constants import *

FTF_hexaddr = 'A4064C'

# open file to read in ADS-B data
#myADSBfilename = "../logged_data/logged_ADSB_data_2021_03_12_0620.txt"
myADSBfilename = "../logged_data/logged_ADSB_data_2021_03_13_0906.txt"

hex_addrs = np.array([])
llas = np.empty((0,3), float)
time_strs = np.array([])
FTF_llas = np.empty((0,3), float)
FTF_times = np.array([])
with open(myADSBfilename, 'r') as reader:
    for line in reader:
        # create a list of items with delimter = space
        line = line.split(" ")
        
        hex_addr = line[0]
        lla = np.array([ line[1:3+1] ], dtype=float)
        time = line[4]+" "+line[5]
        
        # append the callsign
        hex_addrs = np.append(hex_addrs, hex_addr)
        llas = np.append(llas, lla, axis=0)
        time_strs = np.append(time_strs, time)
        
        #print(hex_addr, FTF_hexaddr)
        
        if (hex_addr == FTF_hexaddr):
            #print("IN HERE")
            FTF_llas = np.append(FTF_llas, lla, axis=0)
            FTF_times = np.append(FTF_times, time)
        

print(FTF_llas)


# define figure
fig = plt.figure(1)
#plt.plot(FTF_llas[...,1], FTF_llas[...,0], 'k')
plt.plot(llas[...,1], llas[...,0], 'k.')
plt.plot(QTH_LON, QTH_LAT, 'rs', markersize=8)
plt.xlabel('Longitude (deg)')
plt.ylabel('Latitude (deg)')

