import numpy as np

def GetENUProjectionVecs(origin_ecef_vec):

    ###############################################
    # get local ENU unit vectors at my origin
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
