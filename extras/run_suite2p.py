import numpy as np
import sys
from suite2p.run_s2p import run_s2p, default_ops

def run_suite2p(db, out_path, fs, nplanes):
	default = default_ops()
	default2 = {
		'save_path0': out_path,
		'delete_bin': False,
		'look_one_level_down': True,
		'data_path': db['in_dir'],
		'nplanes': nplanes,
		'fs': fs,
		'save_mat': True,
		'reg_tif': False,
		'expts': db['expts'],
		'raw': True,
	}

	if 'ops' in db:
		opts = db['ops']
	else:
		opts = {}

	ops = {**default, **default2, **opts}

	db = {}

	print(ops)

	ops = run_s2p(ops=ops, db=db)
	return ops
