import numpy as np

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
