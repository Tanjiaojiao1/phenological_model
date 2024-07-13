import numpy as np
import math
from pylab import *

import numpy as np
import math

'''
Three temperature response functions are not normalized
in order to directly calculate the accumulated effective heat.
'''

def T_base_opt(T, Tbase, Topt):
    '''
    T: the daily average temperature
    Tbase: the base temperature. Tbase=8
    Topt: the optimum temperature. Topt=30
    '''
    return np.interp(T,[Tbase,Topt],[0,Topt-Tbase])

def T_base_op_ceiling(T, Tbase, Topt_low,Topt_high, Tcei):
    '''
    Tbase=8, Topt_low=25,Topt_high=35, Tcei=42
    Topt_low: the lower optimum temperature.
    Topt_high: the upper optimum temperature.
    Tcei: Upper threshold temperature for development
    '''
    if T < Tbase or T > Tcei:
        return 0
    elif T >= Tbase and T <= Topt_low:
        return (T- Tbase)
    elif T > Topt_low and T < Topt_high:
        return (Topt_high - Topt_low)
    else:  # This covers the case when T > Topt_high and T <= Tcei
        return (T - Topt_high)


def Wang_engle(T, Tbase, Topt, Tcei):
    '''
    Wang and Engle 1998, Agircultual systems
    Tbase=8, Topt=30, Tcei=42.
    '''
    thermal = 0
    if T <= Tbase or T >= Tcei:
        return thermal
    else:
        alpha = math.log(2, ) / (math.log((Tcei - Tbase) / (Topt - Tbase)))
        thermal = (2 * ((T - Tbase) ** alpha) * (Topt - Tbase) ** alpha - (T - Tbase) ** (2 * alpha)) / (
                (Topt - Tbase) ** (2 * alpha))
        return thermal * (T - Tbase)
