import numpy as np

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
