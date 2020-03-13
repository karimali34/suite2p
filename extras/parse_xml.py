#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  5 16:21:15 2018

@author: karim
"""

import xml
import numpy as np

def parse_xml(in_file):
    e = xml.etree.ElementTree.parse(in_file).getroot()
    lsm = e.find('LSM')
    streaming = e.find('Streaming')
    zstage = e.find('ZStage')
    timelapse = e.find('Timelapse')
    x = int(lsm.attrib['pixelX'])
    y = int(lsm.attrib['pixelY'])
    fr =  float(lsm.attrib['frameRate'])
    #num_frames = int(streaming.attrib['frames'])
    num_frames = int(timelapse.attrib['timepoints'])
    num_planes = int(zstage.attrib['steps']) + int(streaming.attrib['flybackFrames']) if int(streaming.attrib['zFastEnable']) == 1 else 1
    return (x, y, fr, num_frames, num_planes)

if __name__ == '__main__':
    parse_xml('/home/karim/huxley/workspace/suite2p/raw/ca1011/2018_03_22/2/Experiment.xml')