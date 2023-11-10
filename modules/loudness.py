import sys
sys.path.append('..')

import numpy as np
import matplotlib.pyplot as plot
from scipy.fft import fft, fftfreq
from mosqito.utils import load
from mosqito.sq_metrics import loudness_zwst
from mosqito.sq_metrics import loudness_zwst_perseg
from mosqito.sq_metrics import loudness_zwst_freq

from mosqito import COLORS

class Loudness:
    def __init__(self, path, cal):
        self.path = path
        self.cal = cal
        self.size = 10

    def value(self):
        sig, fs = load(self.path, wav_calib = self.cal)
        N, N_spec, bark_axis = loudness_zwst(sig, fs, field_type = "free")
        return N
    
    def timeseg(self):
        sig, fs = load(self.path, wav_calib = self.cal)
        N, N_specific, bark_axis, time_axis = loudness_zwst_perseg(sig, fs, nperseg = len(sig) // self.size * 2)
        time_axis = [0] + time_axis
        N = [0] + N
        return [time_axis, N]