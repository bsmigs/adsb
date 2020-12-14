import numpy as np

def GetENUVelocities(times, enu_vec):

    # calculate position differences from btwn 2 consecutive times
    pos_diff = np.diff(enu_vec, axis=0)
    vec_size = np.shape(pos_diff)

    # calculate time interval
    time_diff = np.diff(times, axis=0).reshape((vec_size[0], 1))

    print(np.shape(times),np.shape(enu_vec),np.shape(pos_diff),np.shape(time_diff))
    print("time_diff = ",time_diff)
    print("pos_diff = ",pos_diff)

    # divide to get time
    enu_vels = np.divide(pos_diff, time_diff)

    return enu_vels
