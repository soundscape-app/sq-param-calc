import sys
sys.path.append('..')

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import stft
from mosqito.utils import load
from mosqito.sq_metrics import roughness_dw, roughness_dw_freq

class Roughness:
    def __init__(self, path, cal):
        self.path = path
        self.cal = cal

    def value(self):
        sig, fs = load(self.path, wav_calib = self.cal)
        r, r_spec, bark, time = roughness_dw(sig, fs, overlap=0)
        return sum(r) / len(r)
    
    def timeseg(self):
        sig, fs = load(self.path, wav_calib = self.cal)
        r, r_spec, bark, time = roughness_dw(sig, fs, overlap=0)
        return [time, r]