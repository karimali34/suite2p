import numpy as np
import sys
from suite2p.run_s2p import run_s2p, default_ops

def run_suite2p(in_path, out_path, fs, nplanes, opts={}):
	default = default_ops()
	default2 = {
		'save_path0': out_path,
		'delete_bin': True,
		'look_one_level_down': True,
		'data_path': [],
		'nplanes': nplanes,
		'fs': fs,
		'save_mat': True,
		'reg_tif': True
	}

	ops = {**default, **default2, **opts}

	db = {'h5py': in_path}

	print(ops)

	run_s2p(ops=ops, db=db)
