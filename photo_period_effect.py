import numpy as np
import math
from pylab import *
def photoeffect_yin(DL, mu, zeta, ep):
    '''
    DL: Actual daylength
    mu=-15.46, zeta=2.06, ep=2.48
    After standardization processing, 'photoeffect_yin' represents the impact of the photoperiod on development rate,
    with values ranging from 0 to 1.
    '''
    def yin_photo(DL, mu, zeta, ep):
        return math.exp(mu) * (DL) ** zeta * (24 - DL) ** ep
    photo = yin_photo(DL=DL,mu=mu,zeta=zeta,ep=ep)
    max_photo=max([yin_photo(DL,mu,zeta,ep) for DL in np.linspace(1, 24, 100)])
    return photo/max_photo

def photoeffect_wofost(DL,Dc,Do):
    '''
    Dc: the critical day length. Dc=16
    Do: the Optimum day length. Do=12.5
    '''
    return(min(max(0, ((DL-Dc)/(Do-Dc))), 1))


def photoeffect_oryza2000(DL, Dc, PPSE):
    '''
    PPSE: a light-sensitive parameter. PPSE=0.2
    '''
    if DL < Dc:
        PPFAC = 1.
    else:
        PPFAC = 1. - (DL - Dc) * PPSE
        PPFAC = np.min([1., np.max([0., PPFAC])])
    return PPFAC


def Test_photoeffect():
    '''
    To test whether the functions are correct
    '''
    plot(range(0, 24), [photoeffect_wofost(DL=DLm) for DLm in np.linspace(0, 24, 24)])
    show()
def CERES_Rice(psr:float=100,DLc:float=12.5,DL:float=10):
    return (1+psr/136*(DL-DLc))**-1
if __name__ == '__main__':
    Test_photoeffect()

