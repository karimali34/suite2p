#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: karim
"""

# Runs the suite2p pipeline for each item in db from params.py.
#
# run using: python batch_pipeline.py
#
# If you wish to use a different file to create the db variable, provide the path to the file using
# the --params flag
#
# python batch_pipeline.py --params /path/to/params.py

import logging
import argparse
logging.basicConfig(format="%(asctime)s %(relativeCreated)12d [%(filename)s:%(funcName)15s():%(lineno)s] [%(process)d] %(message)s", datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)

parser = argparse.ArgumentParser(description='Run pipeline for Suite2p')
parser.add_argument('-p', '--params', dest='params_fn', nargs=1, help='Location of the params.py file', default='./params.py')
parser.add_argument('-m', '--mode', dest='run_mode', help="Choose to run either the full pipeline (\'all\'), only suite2p (\'suite2p\') or only deconv (\'deconv\')", default='all')
args = parser.parse_args()
params_file = args.params_fn
run_mode = args.run_mode

from parse_xml import parse_xml
from raw2h5 import raw2h5
import os
import glob

with open(params_file) as f:
    code = compile(f.read(), params_file, 'exec')
    exec(code)

for i in db:
    comb_dir = '_'.join(str(x) for x in i['expts'])
    tif_dir = os.path.join(i['tif_dir'], i['mouse_name'], i['date'], comb_dir)
    results_dir = os.path.join(i['results_dir'], i['mouse_name'], i['date'], comb_dir)

    if not os.path.isdir(results_dir):
            logging.info(f'Creating results directory {results_dir}')
            os.makedirs(results_dir)

    if 'abf_dir' in i:
        abf_dir = [ os.path.join(i['abf_dir'], i['mouse_name'], i['date'] + "_" + "{:04d}".format(x) + ".abf") for x in i['expts'] ]
    else:
        abf_dir = None
    print(f'Running expt {i}')
    print(f'Temp directory: {tif_dir}')
    print(f'Results directory: {results_dir}')
    i['in_dir'] = os.path.join(i['raw_dir'], i['mouse_name'], i['date'])
    offset = 1
    nframes = []
    for j in i['expts']:
        in_dir = os.path.join(i['in_dir'], str(j))

        # if not os.path.isdir(tif_dir):
        #     logging.info(f'Creating tif path {tif_dir}')
        #     os.makedirs(tif_dir)

        xml_path = os.path.join(in_dir, "Experiment.xml")
        logging.info(f'Parsing Experiment.xml in {xml_path}')
        if os.path.exists(xml_path):
            (x, y, fr, num_frames, num_planes) = parse_xml(xml_path)
            nframes.append(num_frames)
        else:
            raise ValueError(f"Experiment.xml does not exist at {xml_path}")

        # raw_file = os.path.join(in_dir, 'Image_0001_0001.raw')
        # logging.info(f'Converting {raw_file} to tiffs')
        # if os.path.exists(raw_file):
        #     nb = raw2h5(raw_file, tif_dir, (x, y), num_frames, 500, 1, offset)
        #     offset += nb
        # else:
        #     raise ValueError(f'Problem loading {raw_file}')

    for j in nframes:
        print(j)
        
    if run_mode == 'suite2p' or run_mode == 'all':
        from run_suite2p import run_suite2p
        ops = run_suite2p(i, results_dir, fr/num_planes, num_planes)
        ops = ops[0]
    if run_mode == 'deconv' or run_mode == 'all':
        from deconv import do_deconv
        do_deconv(results_dir, 0.5/fr, nframes, i['expts'], abf_dir, nplanes=num_planes)
    #os.remove(ops['reg_file'])
    #os.remove(tif_dir)
