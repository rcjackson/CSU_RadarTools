"""
#############
csu_misc sub-module of csu_radartools

Contacts
--------
Brenda Dolan (dolan@atmos.colostate.edu)
Paul Hein (hein@atmos.colostate.edu)
Timothy Lang (tjlangco@gmail.com)

References
----------
Lang et al. (2007; JCLIM) - Insect filter

Change Log
----------
v1.1 Major Updates (05/08/2015):
1. Added despeckle() along with a private helper function.
2. Added warnings.warn import.

#############
"""

VERSION = '1.1'

import numpy as np
from warnings import warn

#Biological scatterer thresholds originally created using NAME data
DEFAULT_DZ_RANGE = [ [-100,10], [10,15], [15,20], [20,25], [25,30], [30,35] ]
DEFAULT_DR_THRESH = [1, 1.3, 1.7, 2.1, 2.5, 2.8]

def insect_filter(dz, zdr, mask=None, dz_range=DEFAULT_DZ_RANGE,
                  dr_thresh=DEFAULT_DR_THRESH, bad=-32768):
    """
    Returns a mask that identifies potentially suspect gates due to presence of
    biological scatterers.
    """
    #Define generic mask if none provided
    if mask is None:
        mask = np.logical_or(dz == bad, zdr == bad)
    cond = []
    for i, thresh in enumerate(dr_thresh):
        dz_subrange = dz_range[i]
        cond_dz = np.logical_and(dz > dz_subrange[0], dz <= dz_subrange[1])
        sub_cond = np.logical_and(cond_dz, zdr >= thresh)
        cond.append(sub_cond)
    store_cond = mask
    for sub_cond in cond:
        store_cond = np.logical_or(store_cond, sub_cond)
    return store_cond

def second_trip_filter_magnetron(vr, bad=-32768):
    """
    With magnetron transmitters, there is no coherent Doppler signature in 
    second trip. Thus, if velocity is missing but there is echo, that echo is 
    likely second trip.
    """
    return vr == bad

def differential_phase_filter(sdp, thresh_sdp=12):
    """
    Filter out gates with large standard deviations of differential phase.
    Note: thresh_sdp can be an array the same size as sdp.
    """
    return sdp > thresh_sdp

def despeckle(data, bad=-32768, ngates=4):
    """
    data = 1-D or 2-D array of radar data (e.g., reflectivity) to despeckle.
           If 1-D, should be a single ray. If 2-D, first dimension should be 
           azimuth/elevation and second should be range.
    bad = Bad data value to check against
    ngates = Number of contiguous good data gates required along ray for no
             masking to occur
             
    Returns mask w/ same shape as data. True = bad.
    """
    if not hasattr(data, '__len__'):
        warn('Does not work with scalars, #Failing ...')
        return
    if np.ndim(data) == 2:
        mask = data != bad
        for az in xrange(np.shape(data)[0]):
            mask[az, :] = _despeckle_ray(data[az, :], bad, ngates)
    elif np.ndim(data) == 1:
        mask = _despeckle_ray(data, bad, ngates)
    else:
        warn('Need 1- or 2-D array, #Failing ...')
        return
    return mask

def _despeckle_ray(ray, bad, ngates):
    """
    Arguments similar to despeckle(). Should only be sent rays.
    """
    rcp = 1.0 * ray
    count = 0
    for i in xrange(len(rcp)):
        if rcp[i] != bad:
            count += 1
        else:
            if count <= ngates:
                for j in np.arange(i-count, i, 1, dtype=np.int32):
                    ray[j] = bad
            count = 0
    return ray == bad
