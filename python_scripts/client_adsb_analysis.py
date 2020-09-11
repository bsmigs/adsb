import socket
import pyproj
import os
import time
import datetime
import numpy as np
import random
import matplotlib.pyplot as plt
from GetENUCoords import *
from GetENUProjectionVecs import *
from GetECEFPositionVectors import *
from GetENUVelocities import *
from GetHeadings import *
#import sqlite3
#from sqlite3 import Error
from mpl_toolkits.basemap import Basemap
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation


HOST 				= "192.168.1.24" # RPi IP address
PORT 				= 30003 # dump1090 port we are listening to
BUFFER_SIZE 		= 1024 # make it nice and big
NUM_MAX_DATA 		= 50 # number of aircraft to cache
QTH_LAT 			= 42.647690 # my home's latitude
QTH_LON 			= -71.253783 # my home's longitude
LOGAN_LAT 			= 42.3656 # Logan latitude
LOGAN_LON 			= -71.0096 # Logan longitude
MANCHESTER_LAT		= 42.9297 # Manchester lat
MANCHESTER_LON		= -71.4352 # Manchester lon
QTH_ALT 			= 0 # my home's altitude (need to convert to ASL)
EARTH_RADIUS 		= 6366707.0 # (m)
QTH_COORDS 			= np.mat( [QTH_LAT, QTH_LON, QTH_ALT] )
MAX_TIME_UNOBSERVED = 90 # (sec) amt of time elapsed before removing aircraft from cache
AIRCRAFT_ID_MSG 	= 3


def colors_for_plots():

	N_DIFF_TRACKS = 100

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
	
	

class ADS_B:
	def __init__(self,
				 QTH_LAT,
				 QTH_LON,
    			 QTH_ALT,
    			 NUM_MAX_DATA,
    			 MAX_TIME_UNOBSERVED): 
		self.my_flight_tuple 		= {}
		self.my_stored_data			= {}
		self.QTH_COORDS 			= np.mat( [QTH_LAT, QTH_LON, QTH_ALT] )
		self.QTH_LAT 				= QTH_LAT # my home's latitude
		self.QTH_LON 				= QTH_LON # my home's longitude
		self.NUM_MAX_DATA	 		= NUM_MAX_DATA
		self.MAX_TIME_UNOBSERVED	= MAX_TIME_UNOBSERVED
		self.QTH_ECEF_VEC			= GetECEFPositionVectors(self.QTH_COORDS)
		self.QTH_ENU_VEC			= GetENUProjectionVecs(self.QTH_ECEF_VEC)
		self.color_dict				= {}
		self.global_color_dict		= { 'unused':colors_for_plots(), 'used':[]}
        
        
	def get_num_aircraft(self):
		return len(self.my_flight_tuple)
		
        
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


	def parse_new_data(self,
					   split_line):
    	# using Malcolm Robb's dump1090 format
    	# when executing with "net-sbs-port" option
    	# and parse through the fields
    	
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
			#print "No valid altitude"
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
			heading = -1;
                        
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
		epoch = self.convert_to_epoch(ymd, hms)
    
		# gather needed data into a list
		data = [ [epoch, lat, lon, alt] ]

		return msg_type, hex_addr, data
    

	def initialize_stored_data(self,
							   hex_addr, 
							   data):
							   		   
		max_alt = data[0][3]
		matrix_data = np.mat(data)
		aircraft_lla = matrix_data[0:0+1, 1:3+1]
		aircraft_ecef = GetECEFPositionVectors(aircraft_lla)
		aircraft_enu = np.subtract(aircraft_ecef, self.QTH_ECEF_VEC) # (m)
		#delta_ecef_vecs = np.subtract(aircraft_ecef, self.QTH_ECEF_VEC) # (m)
		#aircraft_enu = GetENUCoords(delta_ecef_vecs, self.QTH_ENU_VEC) # (m)
		curr_range = float(np.linalg.norm(aircraft_enu[0,:], axis=1))
		epoch = data[0][0]
		stored_data = {'first_observed':epoch, 'last_observed':epoch, \
    				   'max_range':curr_range, 'max_altitude':max_alt, 'max_speed':0}
    
		self.my_stored_data.update( {hex_addr : stored_data} )
		
		# assign the next available plot color to the 
		# aircraft and move that (r,g,b) tuple to the
		# "used" category
		curr_color = self.global_color_dict['unused'][0]
		self.color_dict[ hex_addr ] = curr_color
		self.global_color_dict['used'].append( curr_color )



	def update_stored_data(self,
						   hex_addr, 
						   data):
						   
    	# if we have at least 2 elements, we can begin
    	# computing other quantities from the 2 most recent
    	# data entries
 
		matrix_data = np.mat(data)
    
		aircraft_lla = matrix_data[0:1+1, 1:3+1]
		aircraft_ecef = GetECEFPositionVectors(aircraft_lla)
    
		# get difference between aircraft ECEF and QTH ECEF coords
		#delta_ecef_vecs = np.subtract(aircraft_ecef, self.QTH_ECEF_VEC) # (m)
		aircraft_enu = np.subtract(aircraft_ecef, self.QTH_ECEF_VEC) # (m)
	
		# convert aircraft coords to ENU centered at my QTH
		#aircraft_enu = GetENUCoords(delta_ecef_vecs, self.QTH_ENU_VEC) # (m)
	
		# get ENU velocities
		times = matrix_data[0:1+1, 0]
		#aircraft_velocities = GetENUVelocities(times, aircraft_enu)
		aircraft_velocities = np.mat([100, 100, 100])
	
		# get speeds
		enu_speeds = np.linalg.norm(aircraft_velocities, axis=1)
	
		# get headings
		headings = GetHeadings(self.QTH_ENU_VEC, aircraft_enu);
		
		# current range of aircraft to my QTH
		curr_range = float(np.linalg.norm(aircraft_enu[0,:], axis=1))
    
		stored_data = self.my_stored_data[ hex_addr ]
		if (curr_range > stored_data['max_range']):
			stored_data['max_range'] = curr_range
			
		if (aircraft_lla[0,2] > stored_data['max_altitude']):
			stored_data['max_altitude'] = aircraft_lla[0,2]
                
		if (enu_speeds[0] > stored_data['max_speed']):
			stored_data['max_speed'] = enu_speeds[0]

		most_recent_observed_time = data[0][0]
		stored_data['last_observed'] = most_recent_observed_time
                    
    	# re-save data
		self.my_stored_data[ hex_addr ] = stored_data


	def update_flight_tuple(self, 
							split_line):
							
		msg_type, hex_addr, data = self.parse_new_data(split_line)
        	
		if ( (msg_type == AIRCRAFT_ID_MSG) and (self.my_flight_tuple.has_key(hex_addr)) ):
			values = self.my_flight_tuple[hex_addr]
			data.extend(values) # older values at the back

        	# if we have at least 2 elements, we can begin
        	# computing other quantities from the 2 most recent
        	# data entries
			if (len(data) > 1):
				self.update_stored_data(hex_addr, data)

        	# update until total amount of data equals what's
        	# specified. Otherwise, pop off earliest entry and
        	# move everything up accordingly. (FIFO)
			if (len(data) > NUM_MAX_DATA):
				data.pop(-1) # pop off the oldest element
				
			# update the data entries
			self.my_flight_tuple[hex_addr] = data
				
		elif ( (msg_type == AIRCRAFT_ID_MSG) and (not self.my_flight_tuple.has_key(hex_addr)) ):
        	# if current aircraft not yet observed, store the 
        	# first time it was seen
			self.initialize_stored_data(hex_addr, data)
			
			# update the data entries
			self.my_flight_tuple[hex_addr] = data
			
		elif ( (msg_type != AIRCRAFT_ID_MSG) and (self.my_flight_tuple.has_key(hex_addr)) ):
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

		curr_keys = self.my_stored_data.keys()
		kk = len(curr_keys) - 1 # count backwards so we don't disturb order of earlier elements when deleting
		while (kk >= 0):
			stored_data = self.my_stored_data[curr_keys[kk]]
			curr_time = time.mktime( datetime.datetime.now().timetuple() )
			if (curr_time - stored_data['last_observed'] > MAX_TIME_UNOBSERVED):
				del self.my_flight_tuple[curr_keys[kk]]
				del self.my_stored_data[curr_keys[kk]]
				
				# make the current color available again
				curr_color = self.color_dict[ curr_keys[kk] ]
				self.global_color_dict['used'].remove( curr_color )
				self.global_color_dict['unused'].append( curr_color )

			kk = kk - 1
			
    
                    
	def process_new_messages(self, 
							 curr_line):
							 
    	# sometimes multiple messages arrive at the same
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
	
        	#print "start_idx = ",start_idx,", locations = ", locations,", len(curr_line) = ",len(curr_line)
        	#print split_line

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
			lats = np.append(lats, curr_data[:,1])
			lons = np.append(lons, curr_data[:,2])
			
			#lats.append( curr_data[:,1] )
			#lons.append( curr_data[:,2] )
			#plot_colors.append(self.color_dict[ key ]) 
			
			
		return lats, lons
		

# create ADS-B object
ads_b = ADS_B(QTH_LAT, QTH_LON, QTH_ALT, NUM_MAX_DATA, MAX_TIME_UNOBSERVED)


#------------------------------------------------------------
# set up figure and animation

def enu_to_geodetic(x_enu, y_enu, units):
	if (units == 'km'):
		x_enu *= 1000
		y_enu *= 1000

	ecef = pyproj.Proj(proj='geocent', ellps='WGS84', datum='WGS84')
	lla = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')
	
	# get my QTH's ecef vector derived from lat/lon
	x0_ecef_home, y0_ecef_home, z0_ecef_home = pyproj.transform(lla, ecef, QTH_LON, QTH_LAT, 0, radians=False)
	
	# now assuming ENU coord system centered on my
	# QTH, get the ecef vectors for the box
	x_max_ecef = x0_ecef_home + x_enu
	y_max_ecef = y0_ecef_home + y_enu
	
	x_min_ecef = x0_ecef_home - x_enu
	y_min_ecef = y0_ecef_home - y_enu
	
	lower_lon, lower_lat, lower_alt = pyproj.transform(ecef, lla, x_min_ecef, y_min_ecef, z0_ecef_home, radians=False)
	upper_lon, upper_lat, upper_alt = pyproj.transform(ecef, lla, x_max_ecef, y_max_ecef, z0_ecef_home, radians=False)
	
	return lower_lon, lower_lat, upper_lon, upper_lat

# define/initialize plots for animation

#maxEast_km 	= 200
#maxNorth_km = 200
#myLowerLon, myLowerLat, myUpperLon, myUpperLat = enu_to_geodetic(maxEast_km, maxNorth_km, 'km')
#print myLowerLon, myLowerLat, myUpperLon, myUpperLat

myLowerLon 	= -74.5
myLowerLat 	= 40.5
myUpperLon 	= -68
myUpperLat 	= 46


'''
fig = plt.figure(1)
myMap = Basemap(projection = 'mill', llcrnrlat=myLowerLat, urcrnrlat=myUpperLat, \
                      	llcrnrlon=myLowerLon, urcrnrlon=myUpperLon, resolution='c', \
                      	lat_0=ads_b.QTH_LAT, lon_0=ads_b.QTH_LON)       
myMap.shadedrelief()
ln, = plt.plot([], [], 'ro', markersize=4)
plt.plot(QTH_LON, QTH_LAT, 'kx', markersize=8)
plt.plot(LOGAN_LON, LOGAN_LAT, 'bs', markersize=8)
plt.plot(MANCHESTER_LON, MANCHESTER_LAT, 'gs', markersize=8)
plt.xlim(myLowerLon, myUpperLon)
plt.ylim(myLowerLat, myUpperLat)
plt.xlabel('Longitude (deg)')
plt.ylabel('Latitude (deg)')
plt.ion()
'''

	
fig = plt.figure(1)
#ax = fig.add_subplot(111)
# miller projection
myMap = Basemap(projection = 'mill', llcrnrlat=myLowerLat, urcrnrlat=myUpperLat, \
                      	llcrnrlon=myLowerLon, urcrnrlon=myUpperLon, resolution='c', \
                      	lat_0=ads_b.QTH_LAT, lon_0=ads_b.QTH_LON)       
myMap.shadedrelief()
x0, y0 = myMap([ads_b.QTH_LON], [ads_b.QTH_LAT])
x1, y1 = myMap([LOGAN_LON], [LOGAN_LAT])
x2, y2 = myMap([MANCHESTER_LON], [MANCHESTER_LAT])
myMap.plot(x0, y0, 'kx', x1, y1, 'bs', x2, y2, 'gs', markersize=8, latlon=False)[0]
point, = myMap.plot([], [], 'ro', markersize=4)
plt.xlabel('Longitude (deg)')
plt.ylabel('Latitude (deg)')

def animate(ii):    
	lats, lons = ads_b.get_current_lats_lons()

    # convert lat/lon to x/y coords on map
	x_list, y_list = myMap(lons, lats)
	point.set_data(x_list, y_list)
    
	return point,

	
	
def plot_updates():
	# get current lats/lons
	lats, lons = ads_b.get_current_lats_lons()
	
	# convert lat/lon to x/y coords on map
	x_list, y_list = myMap(lons, lats)
	point.set_data(x_list, y_list)
	point.set_marker('o')
	point.set_markerfacecolor('r')
	point.set_markeredgecolor('r')
	point.set_markersize(4)
	
	'''
	for key in ads_b.my_flight_tuple:
		curr_data = np.array(ads_b.my_flight_tuple[ key ])    
		rgb_color = ads_b.color_dict[ key ]
		
		lats = curr_data[:,1]
		lons = curr_data[:,2]
		x_list, y_list = myMap(lons, lats)
		point.set_data(x_list, y_list)
		point.set_marker('o')
		point.set_markersize(4)
		point.set_markerfacecolor(rgb_color)
		point.set_markeredgecolor(rgb_color)
	'''
    
    
# create and open a socket connection
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print "Socket made..."
s.connect( (HOST, PORT) )
print "Socket connected..."


num_current_aircraft = 0
max_range = -1
max_range_hex_addr = ''
try:
	while (True):
		# grab current buffer
		curr_line = s.recv(BUFFER_SIZE)
		
		#print curr_line

		# process new messages
		ads_b.process_new_messages(curr_line)

		# see if we've found any new aircraft in the sky		
		num_previous_aircraft = ads_b.get_num_aircraft()
		if (num_current_aircraft != num_previous_aircraft):
			ts = datetime.datetime.now()
			num_current_aircraft = num_previous_aircraft
			print "time = ",ts,"; Number of distinct aircraft seen = ", num_current_aircraft
			
		# display farthest seen aircraft
		for key in ads_b.my_flight_tuple.keys():
			data = ads_b.my_stored_data[key]
			range = data['max_range']
			if (range > max_range):
				max_range = range 
				max_range_hex_addr = key
				print "ICAO address",max_range_hex_addr,"is farthest plane at range",max_range/1000,'(km)'
			
		# plot the new data
		plot_updates()
		plt.draw()
		plt.pause(0.001)
		
except KeyboardInterrupt:     
	print "Exiting out of program..."
	s.close()




    


    
