#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  5 14:53:25 2018

@author: karim
"""

import os
from skimage import io
import numpy as np
import logging
import tiffile

def raw2tiff(in_file, out_path, dims, num_frames, block_size=128, nplanes=1, offset=1):
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
                fnames.append(os.path.join(out_path, f'raw{str(i+offset).zfill(6)}.tif'))
            else:
                for j in range(nplanes):
                    fnames.append(os.path.join(out_path, f'plane{j}raw{str(i+offset).zfill(6)}.tif'))
            
            for fname in fnames:
                if os.path.exists(fname):
                    logging.info(f'Skipping {fname} since it already exists')
                    fp.seek(count*2)
                    continue
                
            data = np.fromfile(fp, dtype='uint16', count=count)
            num_loaded = int(len(data) / (dims[0] * dims[1]))
            logging.info(f'Num frames loaded: {num_loaded}')
            data = np.reshape(data, (x, y, num_loaded), order='F')
            data = np.rot90(data, k=1, axes=(0, 1))
            data = np.transpose(data, (2, 1, 0))
            for j in range(nplanes):
                logging.info(f'Writing to {fnames[j]}')
                #io.imsave(fnames[j], data[j::nplanes, :, :])
                tiffile.imwrite(fnames[j], data[j::nplanes, :, :], photometric='minisblack')
    return num_blocks
            
if __name__ == "__main__":
    raw2tiff('/media/storage/data/rui/mPFC10/2019_05_16/1/Image_0001_0001.raw', '/media/storage/data/rui/mPFC10/2019_05_16/1/tif/', (800, 800), 17000, 200, 1)