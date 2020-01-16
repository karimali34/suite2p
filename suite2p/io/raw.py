import gc
import numpy as np
from natsort import natsorted
import math, time
import glob, h5py, os, json
from scipy import signal
from scipy import stats, signal
from scipy.sparse import linalg
import scipy.io
from . import utils
import xml

def raw_to_binary(ops):
    """  finds h5 files and writes them to binaries

    Parameters
    ----------
    ops : dictionary
        'nplanes', 'h5_path', 'h5_key', 'save_path', 'save_folder', 'fast_disk',
        'nchannels', 'keep_movie_raw', 'look_one_level_down'

    Returns
    -------
        ops1 : list of dictionaries
            'Ly', 'Lx', ops1[j]['reg_file'] or ops1[j]['raw_file'] is created binary

    """

    ops1 = utils.init_ops(ops)

    nplanes = ops1[0]['nplanes']
    nchannels = ops1[0]['nchannels']



    # open all binary files for writing
    # ops1, h5list, reg_file, reg_file_chan2 = utils.find_files_open_binaries(ops1, True)

    reg_file = []
    reg_file_chan2=[]

    for ops in ops1:
        nchannels = ops['nchannels']
        if 'keep_movie_raw' in ops and ops['keep_movie_raw']:
            reg_file.append(open(ops['raw_file'], 'wb'))
            if nchannels>1:
                reg_file_chan2.append(open(ops['raw_file_chan2'], 'wb'))
        else:
            reg_file.append(open(ops['reg_file'], 'wb'))
            if nchannels>1:
                reg_file_chan2.append(open(ops['reg_file_chan2'], 'wb'))

    if 'expts' in ops:
        rawlist = []
        for i in ops['expts']:
            rawlist.append(os.path.join(ops['data_path'], str(i)))
    else:
        rawlist = os.path.join(ops['data_path'])

    nbatch = nplanes*nchannels*math.ceil(ops1[0]['batch_size']/(nplanes*nchannels))

    iall = 0

    for ir,r in enumerate(rawlist):
        raw_fn = os.path.join(r, 'Image_0001_0001.raw')
        expt_file = os.path.join(r, 'Experiment.xml')
        if not os.path.isfile(expt_file):
            raise(f'Experiment.xml not found for in {r}')
        e = xml.etree.ElementTree.parse(expt_file).getroot()
        streaming = e.find('Streaming')
        lsm = e.find('LSM')
        timelapse = e.find('Timelapse')

        nframes_all = int(streaming.attrib['frames'])
        nts = int(timelapse.attrib['timepoints'])
        x = int(lsm.attrib['pixelX'])
        y = int(lsm.attrib['pixelY'])

        with open(raw_fn, 'rb') as f:
            nblocks = math.ceil(nframes_all/nbatch)
            for j in range(nblocks):
                data = np.fromfile(f, dtype='uint16', count=x*y*nbatch)
                num_loaded = int(len(data) / (x * y))
                data = np.reshape(data, (x, y, num_loaded), order='F')
                data = np.rot90(data, k=1, axes=(0, 1))
                data = np.transpose(data, (2, 1, 0))
                for k in range(0, nplanes):
                    if iall == 0:
                        ops1[k]['meanImg'] = np.zeros((x, y), np.float32)
                        ops1[k]['nframes'] = 0
                    idx = np.arange(k, num_loaded, nplanes*nchannels)
                    im2write = data[idx, :, :].astype(np.int16)
                    reg_file[k].write(bytearray(im2write))
                    ops1[k]['meanImg'] += im2write.astype(np.float32).sum(axis=0)
                    ops1[k]['nframes'] += im2write.shape[0]
                iall += 1

    # write ops files
    do_registration = ops1[0]['do_registration']
    do_nonrigid = ops1[0]['nonrigid']
    for ops in ops1:
        ops['Lx'] = im2write.shape[1]
        ops['Ly'] = im2write.shape[2]
        if not do_registration:
            ops['yrange'] = np.array([0,ops['Ly']])
            ops['xrange'] = np.array([0,ops['Lx']])
        ops['meanImg'] /= ops['nframes']
        if nchannels>1:
            ops['meanImg_chan2'] /= ops['nframes']
        np.save(ops['ops_path'], ops)
    # close all binary files and write ops files
    for j in range(0,nplanes):
        reg_file[j].close()
        if nchannels>1:
            reg_file_chan2[j].close()
    return ops1
