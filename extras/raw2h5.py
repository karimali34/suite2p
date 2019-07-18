#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 21:38:00 2019

@author: karim
"""

import os
from skimage import io
import numpy as np
import logging
import h5py

def raw2h5(in_file, out_path, dims, num_frames, block_size=128, nplanes=1, offset=1):
    logging.basicConfig(format="%(relativeCreated)12d [%(filename)s:%(funcName)10s():%(lineno)s] [%(process)d] %(message)s", level=logging.DEBUG)
    x = dims[0]
    y = dims[1]
    num_blocks = np.ceil(num_frames / block_size / nplanes)
    num_blocks = num_blocks.astype(np.int32).item()
    logging.info(f'Reading {in_file}')    
    with open(in_file, "rb") as fp:
        for i in range(num_blocks):
            count = x*y*block_size*nplanes
            fnames = []
            if nplanes == 1:
                fnames.append(os.path.join(out_path, f'raw{str(i+offset).zfill(6)}.h5'))
            else:
                for j in range(nplanes):
                    fnames.append(os.path.join(out_path, f'plane{j}raw{str(i+offset).zfill(6)}.h5'))
            
            f_exist = False
            for fname in fnames:
                if os.path.exists(fname):
                    logging.info(f'Skipping {fname} since it already exists')
                    fp.seek(count*2)
                    f_exist = True

            if f_exist:
                continue
                
            data = np.fromfile(fp, dtype='uint16', count=count)
            logging.debug('Current position: {}'.format(fp.tell()))
            num_loaded = int(len(data) / (dims[0] * dims[1]))
            logging.info(f'Num frames loaded: {num_loaded}')
            data = np.reshape(data, (x, y, num_loaded), order='F')
            data = np.rot90(data, k=1, axes=(0, 1))
            data = np.transpose(data, (2, 1, 0))
            logging.debug('First 10 elements: ')
            logging.debug(data[0:10, 0, 0])
            for j in range(nplanes):
                logging.info(f'Writing to {fnames[j]}')
                with h5py.File(fnames[j], 'w') as hf:
                    hf.create_dataset('data', data=data)
    return num_blocks
