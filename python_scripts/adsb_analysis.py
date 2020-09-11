import datetime
import matplotlib.pyplot as plt
import numpy as np
import sys


def read_file(file_name):
    my_file = open(file_name,'r')
    lines = my_file.readlines()
    my_file.close()

    # create empty dictionary
    # key = flight ID
    # value = relevant params
    
    lla_dict = {}
    shv_dict = {} 

    for line in lines:
        split_line = line.split(',') # split strings based on commas from file
        msg_type = int(split_line[1])

        str_filled = False
        if (split_line[14]):
            str_filled = True

        if ((msg_type == 3) & (str_filled)):
            # this msg type carries lat/lon/alt info.
            # sometimes msg 3 does not carry lat/lon
            # so need to check. Only keep it if it does
           
            flightID = split_line[4]
            alt = float(split_line[11])
            lat = float(split_line[14])
            lon = float(split_line[15])
            time = float(split_line[22])

            if (flightID not in lla_dict):
                lla_dict[flightID] = [[time, lat, lon, alt]]
            else:
                curr_vals = lla_dict[flightID]
                curr_vals.append([time, lat, lon, alt])
                lla_dict[flightID] = curr_vals
            
        elif (msg_type == 4):

            flightID = split_line[4]
            time = float(split_line[22])
            speed = float(split_line[12])
            heading = float(split_line[13])
            vertical_rate = float(split_line[16])
            
            if (flightID not in shv_dict):
                shv_dict[flightID] = [[time, speed, heading, vertical_rate]]
            else:
                curr_vals = shv_dict[flightID]
                curr_vals.append([time, speed, heading, vertical_rate])
                shv_dict[flightID] = curr_vals
        else:
            continue

    # get rid of any flight IDs in the speed heading velocity
    # dictionary but NOT in the lat lon alt dictionary
    for key in shv_dict.keys():
        if key not in lla_dict:
            shv_dict.pop(key, None)
    
    my_tuple = (lla_dict, shv_dict)
    return my_tuple





def GetECEFPositionVectors(lla):

    EARTH_RADIUS = 6366707.0 # (m)

    #phi = np.subtract(90, lats)
    #phi = np.deg2rad(phi)

    phi = np.deg2rad(lla[:,0])
    theta = np.deg2rad(lla[:,1])
            
    sinphi = np.sin(phi)
    cosphi = np.cos(phi)
    
    sintheta = np.sin(theta)
    costheta = np.cos(theta)
    
    angle_vec = np.mat(np.zeros(np.shape(lla)))
    angle_vec[:,0] = np.multiply(cosphi, costheta)
    angle_vec[:,1] = np.multiply(cosphi, sintheta)
    angle_vec[:,2] = sinphi
        
    radius_vec = np.add(EARTH_RADIUS, lla[:,2])
    # need to repeat this 3 times (for 3 elements
    # of angle_vec
    #radius_vec = np.repeat(radius_vec, 3, axis=1)
    ecef_vec = np.multiply(radius_vec, angle_vec)
    
    return ecef_vec




def ConvertQTHToLocalCoords(origin_ecef_vec):
    # repeat QTH vec so its same size as current
    # flight lat/lon/alts
    
    ###############################################
    # get local ENU unit vectors at my QTH position
    ###############################################
    
    # get the up direction unit vector
    norm_factor = np.linalg.norm(origin_ecef_vec)
    up_hat = np.divide(origin_ecef_vec, norm_factor)

    # get the east direction unit vector
    ecef_z_vec = np.array([0, 0, 1])
    east_vec = np.cross(ecef_z_vec, up_hat)
    norm_factor = np.linalg.norm(east_vec)
    east_hat = np.divide(east_vec, norm_factor)

    # get the north direction unit vector
    north_vec = np.cross(east_hat, up_hat)
    norm_factor = np.linalg.norm(north_vec)
    north_hat = np.divide(north_vec, norm_factor)

    enu_vec = np.mat(np.zeros((3, 3)))
    enu_vec[0,:] = east_hat
    enu_vec[1,:] = north_hat
    enu_vec[2,:] = up_hat

    return enu_vec




def GetENUCoords(delta_ecef_vecs, origin_enu_vec):

    # grab the ENU unit vectors (in ECEF frame)
    east_hat = origin_enu_vec[0,:]
    north_hat = origin_enu_vec[1,:]
    up_hat = origin_enu_vec[2,:]

    ecef_size = np.shape(delta_ecef_vecs)
    east_hat = np.repeat(east_hat, ecef_size[0], axis=0)
    
    # calculate projections of aircraft ECEF onto local ENU axes
    axis_dim = 1
    east_vec = np.multiply(east_hat, delta_ecef_vecs).sum(axis_dim)
    north_vec = np.multiply(north_hat, delta_ecef_vecs).sum(axis_dim)
    up_vec = np.multiply(up_hat, delta_ecef_vecs).sum(axis_dim)
    
    # store result
    enu_vec = np.mat(np.zeros(ecef_size))
    enu_vec[:,0] = east_vec
    enu_vec[:,1] = north_vec
    enu_vec[:,2] = up_vec

    return enu_vec




def GetENUVelocities(times, enu_vec):

    # calculate position differences from btwn 2 consecutive times
    pos_diff = np.diff(enu_vec, axis=0)
    vec_size = np.shape(pos_diff)

    # calculate time interval
    time_diff = np.diff(times).reshape((vec_size[0], 1))

    # divide to get time
    enu_vels = np.divide(pos_diff, time_diff)

    return enu_vels




def GetHeadings(origin_enu_vec, enu_vec):

    # project aircraft coords onto E-N plane and normalize
    proj_aircraft = enu_vec[:,0:2]
    norm_factor = np.linalg.norm(proj_aircraft, axis=1, keepdims=True) # keep it an (N x 1) entity
    proj_aircraft = np.divide(proj_aircraft, norm_factor)

    # define local north unit vector and repeat as many
    # times necessary
    north = np.mat([0, 1])
    enu_vec_size = np.shape(enu_vec)
    north = np.repeat(north, enu_vec_size[0], axis=0)

    # get the headings by taking dot product of north
    # unit vector with aircraft projected coords
    axis_dim = 1
    dot_prod = np.multiply(north, proj_aircraft).sum(axis_dim)
    headings = np.arccos(dot_prod)

    # the dot product will ALWAYS give us the smallest angle
    # between 2 vectors. If we wish to capture the other one
    # need to put in a check that if the east coordinate is < 0
    # we then take (2*pi - original heading)
    condlist = [proj_aircraft[:,0] < 0, proj_aircraft[:,0] >= 0]
    choicelist = [2*np.pi - headings, headings]
    headings = np.select(condlist, choicelist)
    headings = np.rad2deg(headings)

    return headings




################################################

my_tuple = read_file('../data_files/myADSBFile7.dat')
lla_keys = my_tuple[0].keys()
lla = my_tuple[0]

# define my QTH coords
QTH_coords = np.mat([42.647690, -71.253783, 0])
QTH_ecef_vec = GetECEFPositionVectors(QTH_coords)
QTH_enu_vec = ConvertQTHToLocalCoords(QTH_ecef_vec)

for key in lla_keys:
    curr_flight = lla[key]
    
    # get the times and convert from epoch to relative
    t0 = curr_flight[0][0]
    times = np.mat([row[0] for row in curr_flight]) # (s)

    # make an N x 3 array
    aircraft_lla = np.mat([[row[1], row[2], row[3]] for row in curr_flight])

    # get aircraft position vectors
    ecef_pos_vecs = GetECEFPositionVectors(aircraft_lla) # (m)

    # get difference between aircraft ECEF and QTH ECEF coords
    delta_ecef_vecs = np.subtract(ecef_pos_vecs, QTH_ecef_vec) # (m)

    # convert aircraft coords to ENU centered at my QTH
    aircraft_ENU_coords = GetENUCoords(delta_ecef_vecs, QTH_enu_vec) # (m)

    # get ENU velocities
    enu_velocities = GetENUVelocities(times, aircraft_ENU_coords)

    # get total velocity
    enu_speeds = np.linalg.norm(enu_velocities, axis=1)

    # get bearings
    bearings = GetHeadings(QTH_enu_vec, aircraft_ENU_coords);
    
    #plt.figure
    #plt.plot(times, ranges_from_QTH/1000.0, 's-')
    #plt.xlabel('Time (min)');
    #plt.ylabel('Range from QTH (km)')
    #plt.title(key)

    #plt.show()
    

    
    sys.exit(0)
    
    #plt.subplot(211)
    #plt.plot(lons, lats, 'o', markersize=1)
    #plt.xlabel('Longitude (deg)')
    #plt.ylabel('Latitude (deg)')

    #plt.subplot(212)
    #plt.plot(times, alts, 'o', markersize=1)
    #plt.axis([0, 15, 0, 60])
    #plt.xlabel('Time (min)')
    #plt.ylabel('Altitude (kft)')
    

    

plt.figure(2)
shv_keys = my_tuple[1].keys()
shv = my_tuple[1]
for key in shv_keys:
    p1 = shv[key]

    t0 = p1[0][0]
    times = [(row[0] - t0) / 60 for row in p1]    
    speeds = [row[1] for row in p1]
    headings = [row[2] for row in p1]
    vert_rates = [row[3] for row in p1]
    

    plt.subplot(211)
    plt.plot(times, speeds, 'o', markersize=1)
    plt.axis([0, 15, 0, 600])
    plt.xlabel('Time (min)')
    plt.ylabel('Speed (mph??)')

    
    plt.subplot(212)
    plt.plot(times, headings, 'o', markersize=1)
    plt.axis([0, 15, 0, 360])
    plt.xlabel('Time (min)')
    plt.ylabel('Heading (deg)')
    
plt.show()


time1 = p1[4][0]
print time1

p2 = datetime.datetime.fromtimestamp(time1).strftime('%c')
print p2

        
        
        

    
