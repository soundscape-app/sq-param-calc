import sys
sys.path.append('..')

import numpy as np
import matplotlib.pyplot as plot
from scipy.fft import fft, fftfreq
from mosqito.utils import load
from mosqito.sq_metrics import sharpness_din_st
from mosqito.sq_metrics import sharpness_din_perseg
from mosqito.sq_metrics import sharpness_din_from_loudness
from mosqito.sq_metrics import sharpness_din_freq
from mosqito import COLORS

class Sharpness:
    def __init__(self, path, cal):
        self.path = path
        self.cal = cal
        self.size = 10

    def value(self):
        sig, fs = load(self.path, wav_calib = self.cal)
        sharpness = sharpness_din_st(sig, fs, weighting="din")
        return sharpness
    
    def timeseg(self):
        sig, fs = load(self.path, wav_calib = self.cal)
        sharpness, time_axis = sharpness_din_perseg(sig, fs, nperseg = len(sig) // self.size * 2, weighting="din")
        print(time_axis)
        print(sharpness) 
        time_axis = [0] + time_axis
        sharpness = [0] + sharpness
        return [time_axis, sharpness]