#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  5 16:05:47 2018

@author: karim
"""
# This file is used to describe experiments you wish to batch process.
# The result of running this file should be a variable named 'db' which is an array of dicts
# with the fields:
#     - mouse_name - name of the folder containing the experiment in the raw_dir directory
#     - date - a string naming the date directory within the mouse_name directory
#     - expts - a list of the experiments recorded on the date to concatenate and analyze
#     - raw_dir - root directory containing the raw data
#     - tif_dir - output directory for the raw to hdf5 converter
#     - results_dir - output results directory
#     - ops - custom parameters to control suite2p output (optional)
# The script will look in the folder: raw_dir/mouse_name/date/expts[0] for the file Image_0001_0001.raw and Experiment.xml


db = []

db.append({
    "mouse_name": "rsc036",
    "date": "2017_11_09",
    "expts": [1],
    "raw_dir": "/mnt/polaris1/scratch",
    "tif_dir": "/mnt/storage/temp/tif",
    "results_dir": "/mnt/storage/temp/results",
    "abf_dir": "/mnt/mohaj1/homes/dun.mao/behavior",
    "ops": {'save_mat': False}
})
