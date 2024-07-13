import numpy as np
import math
from pylab import *
def photoeffect_yin(DL, mu, zeta, ep):
    '''
    DL: Actual daylength
    mu, zeta, and ep are the model parameters.
    After standardization processing, 'photoeffect_yin' represents the impact of the DL on development rate,
    with values ranging from 0 to 1.
    '''
    def yin_photo(DL, mu, zeta, ep):
        return math.exp(mu) * (DL) ** zeta * (24 - DL) ** ep
    photo = yin_photo(DL=DL,mu=mu,zeta=zeta,ep=ep)
    max_photo=max([yin_photo(DL,mu,zeta,ep) for DL in np.linspace(1, 24, 100)])
    return photo/max_photo


def photoeffect_oryza2000(DL, Dc, PPSE):
    '''
    PPSE: a light-sensitive parameter.
    '''
    if DL < Dc:
        PPFAC = 1.
    else:
        PPFAC = 1. - (DL - Dc) * PPSE
        PPFAC = np.min([1., np.max([0., PPFAC])])
    return PPFAC


def CERES_Rice(psr,Do,DL):
    if DL < Do:
        PPFAC = 1.
    else:
        PPFAC = (1+psr/136*(DL-Do))**-1
    return PPFAC


