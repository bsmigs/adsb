import numpy as np

EARTH_RADIUS = 6366707.0 # (m)

def GetECEFPositionVectors(lla):
    #phi = np.subtract(90, lats)
    #phi = np.deg2rad(phi)
    
    lats = lla[:,0]
    lons = lla[:,1]

    phi = np.deg2rad(lats)
    theta = np.deg2rad(lons)
            
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
