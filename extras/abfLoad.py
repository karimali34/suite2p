"""
Read and process abf behaviour files in python
Right now, only extracts the frame time-stamps
Will implement full behaviour extraction methods in future

direct complaints to HaoRan Chang
2019-09-19
"""

import pyabf
import numpy as np

class abfLoad:
    def __init__(self, fn, frameCh=0):
        self.abf = pyabf.ABF(fn)
        self.abf.setSweep(sweepNumber=0, channel=frameCh)

    def frame_ts(self):
        if "_abfLoad__ts" in self.__dict__:
            return self.__ts
        thres = 3
        idx = np.multiply(self.abf.sweepY < thres, 1)
        idx = np.diff(idx)
        idx = idx > 0
        idx = np.append(False, idx)
        self.__ts = self.abf.sweepX[ idx ]
        return self.__ts

    def Fs(self):
        if "_abfLoad__Fs" in self.__dict__:
            return self.__Fs
        self.__Fs = 1 / np.median( np.diff(self.frame_ts()) )
        return self.__Fs
